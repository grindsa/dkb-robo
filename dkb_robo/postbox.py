""" Module for handling the DKB postbox. """
import datetime
import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import requests

from dkb_robo.api import JSON_CONTENT_TYPE, DKBRoboError
from dkb_robo.utilities import get_valid_filename

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """ Document data class, roughly based on the JSON API response. """
    # pylint: disable=c0103
    creationDate: str
    expirationDate: str
    retentionPeriod: str
    contentType: str
    checksum: str
    fileName: str
    metadata: Dict[str, str]
    owner: str
    link: str


@dataclass
class Message:
    """ Message data class, roughly based on the JSON API response. """
    # pylint: disable=c0103
    archived: bool
    read: bool
    subject: str
    documentType: str
    creationDate: str
    link: str


@dataclass
class PostboxItem:
    """ Postbox item data class, merging document and message data and providing download functionality. """
    DOCTYPE_MAPPING = {
        "bankAccountStatement": "Kontoauszüge",
        "creditCardStatement": "Kreditkartenabrechnungen",
        "dwpRevenueStatement": "Wertpapierdokumente",
        "dwpOrderStatement": "Wertpapierdokumente",
        "dwpDepotStatement": "Wertpapierdokumente",
        "exAnteCostInformation": "Wertpapierdokumente",
        "dwpCorporateActionNotice": "Wertpapierdokumente",
    }

    id: str
    document: Document
    message: Message

    def mark_read(self, client: requests.Session, read: bool):
        """ Marks the document as read or unread. """
        logger.debug("Set read status of document %s to %s", self.id, read)
        resp = client.patch(
            self.message.link,
            json={"data": {"attributes": {"read": read}, "type": "message"}},
            headers={"Accept": JSON_CONTENT_TYPE, "Content-type": JSON_CONTENT_TYPE}
        )
        resp.raise_for_status()

    def download(self, client: requests.Session, target_file: Path, overwrite: bool = False):
        """
        Downloads the document from the provided link and saves it to the target file.

        :param client: The requests session to use for downloading the document.
        :param target_file: The path where the document should be saved.
        :param overwrite: Whether to overwrite the file if it already exists.
        :return: True if the file was downloaded and saved, False if the file already exists and overwrite is False.
        """
        if not target_file.exists() or overwrite:
            resp = client.get(self.document.link, headers={"Accept": self.document.contentType})
            resp.raise_for_status()

            # create directories if necessary
            target_file.parent.mkdir(parents=True, exist_ok=True)

            with target_file.open('wb') as file:
                file.write(resp.content)

            # compare checksums of file with checksum from document metadata
            if self.document.checksum:
                with target_file.open('rb') as file:
                    checksum = hashlib.md5(file.read()).hexdigest()
                    if checksum != self.document.checksum:
                        logger.warning("Checksum mismatch for %s: %s != %s. Renaming file.", target_file, checksum, self.document.checksum)
                        # rename file to indicate checksum mismatch
                        target_file.rename(target_file.with_name(target_file.name + '.checksum_mismatch'))
            return True
        return False

    def filename(self) -> str:
        """ Returns a sanitized filename based on the document metadata. """
        filename = self.document.fileName

        # Depot related files don't have meaningful filenames but only contain the document id. Hence, we use subject
        # instead and rely on the filename sanitization.
        if 'dwpDocumentId' in self.document.metadata and 'subject' in self.document.metadata:
            filename = self.subject() or self.document.fileName

        if self.document.contentType == 'application/pdf' and not filename.endswith('pdf'):
            filename = f'{filename}.pdf'

        return get_valid_filename(filename)

    def subject(self) -> str:
        """ Returns the subject of the message. """
        return self.document.metadata.get('subject', self.message.subject)

    def category(self) -> str:
        """ Returns the category of the document based on the document type. """
        return PostboxItem.DOCTYPE_MAPPING.get(self.message.documentType, self.message.documentType)

    def account(self, card_lookup: Dict[str, str] = None) -> str:
        """ Returns the account number or IBAN based on the document metadata. """
        if card_lookup is None:
            card_lookup = {}
        account = None
        if 'depotNumber' in self.document.metadata:
            account = self.document.metadata['depotNumber']
        elif 'cardId' in self.document.metadata:
            account = card_lookup.get(self.document.metadata['cardId'], self.document.metadata['cardId'])
        elif 'iban' in self.document.metadata:
            account = self.document.metadata['iban']

        return account

    def date(self) -> str:
        """ Returns the date of the document based on the metadata. """
        date = None
        if 'statementDate' in self.document.metadata:
            date = datetime.date.fromisoformat(self.document.metadata['statementDate'])
        elif 'statementDateTime' in self.document.metadata:
            date = datetime.datetime.fromisoformat(self.document.metadata['statementDateTime'])
        elif 'creationDate' in self.document.metadata:
            date = datetime.date.fromisoformat(self.document.metadata['creationDate'])

        if date is None:
            raise AttributeError("No valid date field found in document metadata.")

        return date.strftime('%Y-%m-%d')


class PostBox:
    """ Class for handling the DKB postbox. """
    BASE_URL = "https://banking.dkb.de/api/documentstorage/"

    def __init__(self, client: requests.Session):
        self.client = client

    def fetch_items(self) -> Dict[str, PostboxItem]:
        """ Fetches all items from the postbox and merges document and message data. """
        def __fix_link_url(url: str) -> str:
            return url.replace("https://api.developer.dkb.de/", PostBox.BASE_URL)

        logger.debug("Fetching messages...")
        response = self.client.get(PostBox.BASE_URL + '/messages')
        response.raise_for_status()
        messages = response.json()

        logger.debug("Fetching documents...")
        response = self.client.get(PostBox.BASE_URL + '/documents?page%5Blimit%5D=1000')
        response.raise_for_status()
        documents = response.json()

        if messages and documents:
            # Merge raw messages and documents from JSON API (left join with documents as base).
            items = {
                doc['id']: PostboxItem(
                    id=doc['id'],
                    document=Document(**doc.get('attributes', {}), link=__fix_link_url(doc['links']['self'])),
                    message=None
                )
                for doc in documents.get('data', [])
            }

            # Add matching message data
            for msg in messages.get('data', []):
                msg_id = msg['id']
                if msg_id in items:
                    items[msg_id].message = Message(**msg.get('attributes', {}), link=__fix_link_url(msg['links']['self']))

            return items
        raise DKBRoboError("Could not fetch messages/documents.")
