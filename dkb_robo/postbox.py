""" Module for handling the DKB postbox. """
import datetime
import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Union
import requests
from dkb_robo.utilities import (
    get_valid_filename,
    filter_unexpected_fields,
    DKBRoboError,
    JSON_CONTENT_TYPE,
)

logger = logging.getLogger(__name__)


@filter_unexpected_fields
@dataclass
class Document:
    """Document data class, roughly based on the JSON API response."""

    # pylint: disable=c0103
    creationDate: Optional[str] = None
    expirationDate: Optional[str] = None
    retentionPeriod: Optional[str] = None
    contentType: Optional[str] = None
    checksum: Optional[str] = None
    fileName: Optional[str] = None
    metadata: Optional[Union[Dict, str]] = None
    owner: Optional[str] = None
    link: Optional[str] = None
    rcode: Optional[str] = None
    documentTypeId: Optional[str] = None


@filter_unexpected_fields
@dataclass
class Message:
    """Message data class, roughly based on the JSON API response."""

    # pylint: disable=c0103
    archived: bool = False
    read: bool = False
    subject: Optional[str] = None
    documentId: Optional[str] = None
    documentType: Optional[str] = None
    creationDate: Optional[str] = None
    link: Optional[str] = None


@filter_unexpected_fields
@dataclass
class PostboxItem:
    """Postbox item data class, merging document and message data and providing download functionality."""

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
        """Marks the document as read or unread."""
        logger.debug("PostboxItem.mark_read(): set document %s to %s", self.id, read)
        resp = client.patch(
            self.message.link,
            json={"data": {"attributes": {"read": read}, "type": "message"}},
            headers={"Accept": JSON_CONTENT_TYPE, "Content-type": JSON_CONTENT_TYPE},
        )
        resp.raise_for_status()

    def check_checsum(self, target_file: Path):
        logger.debug("PostboxItem.check_checsum(): %s", self.id)
        with target_file.open("rb") as file:
            if len(self.document.checksum) == 32:
                computed_checksum = hashlib.md5(file.read()).hexdigest()
            elif len(self.document.checksum) == 128:
                computed_checksum = hashlib.sha512(file.read()).hexdigest()
            else:
                raise DKBRoboError(
                    f"Unsupported checksum length: {len(self.document.checksum)}, {self.document.checksum}"
                )
        if computed_checksum != self.document.checksum:
            logger.warning(
                "Checksum mismatch for %s: %s != %s. Renaming file.",
                target_file,
                computed_checksum,
                self.document.checksum,
            )
            # rename file to indicate checksum mismatch
            suffix = ".checksum_mismatch"
            if not target_file.with_name(target_file.name + suffix).exists():
                # rename file to indicate checksum mismatch
                target_file.rename(target_file.with_name(target_file.name + suffix))
            else:
                logger.warning(
                    "File %s%s already exists. Not renaming.", target_file, suffix
                )

    def download(
        self, client: requests.Session, target_file: Path, overwrite: bool = False
    ):
        """
        Downloads the document from the provided link and saves it to the target file.

        :param client: The requests session to use for downloading the document.
        :param target_file: The path where the document should be saved.
        :param overwrite: Whether to overwrite the file if it already exists.
        :return: True if the file was downloaded and saved, False if the file already exists and overwrite is False.
        """
        logger.debug("PostboxItem.download(): %s to %s", self.id, target_file)
        if not target_file.exists() or overwrite:
            resp = client.get(
                self.document.link, headers={"Accept": self.document.contentType}
            )
            resp.raise_for_status()

            # create directories if necessary
            target_file.parent.mkdir(parents=True, exist_ok=True)

            with target_file.open("wb") as file:
                file.write(resp.content)

            if self.document.checksum:
                # compare checksums of file with checksum from document metadata
                self.check_checsum(target_file)

            return resp.status_code
        return False

    def filename(self) -> str:
        """Returns a sanitized filename based on the document metadata."""
        logger.debug(
            "PostboxItem.filename(): Generating filename for document %s", self.id
        )

        filename = self.document.fileName
        # Depot related files don't have meaningful filenames but only contain the document id. Hence, we use subject
        # instead and rely on the filename sanitization.
        if (
            "dwpDocumentId" in self.document.metadata
            and "subject" in self.document.metadata
        ):
            filename = self.subject() or self.document.fileName

        if self.document.contentType == "application/pdf" and not filename.endswith(
            "pdf"
        ):
            filename = f"{filename}.pdf"

        fname = get_valid_filename(filename)
        logger.debug("PostboxItem.filename() for %s ended with %s", self.id, fname)
        return fname

    def subject(self) -> str:
        """Returns the subject of the message."""
        return self.document.metadata.get("subject", self.message.subject)

    def category(self) -> str:
        """Returns the category of the document based on the document type."""
        return PostboxItem.DOCTYPE_MAPPING.get(
            self.message.documentType, self.message.documentType
        )

    def account(self, card_lookup: Dict[str, str] = None) -> str:
        """Returns the account number or IBAN based on the document metadata."""
        logger.debug("PostboxItem.account() fom document %s", self.id)
        if card_lookup is None:
            card_lookup = {}
        account = None
        if "depotNumber" in self.document.metadata:
            account = self.document.metadata["depotNumber"]
        elif "cardId" in self.document.metadata:
            account = card_lookup.get(
                self.document.metadata["cardId"], self.document.metadata["cardId"]
            )
        elif "iban" in self.document.metadata:
            account = self.document.metadata["iban"]

        logger.debug(
            "PostboxItem.account() for document %s ended with %s", self.id, account
        )
        return account

    def date(self) -> str:
        """Returns the date of the document based on the metadata."""
        logger.debug("PostboxItem.date() for document %s", self.id)
        date = None
        if "statementDate" in self.document.metadata:
            date = datetime.date.fromisoformat(self.document.metadata["statementDate"])
        elif "statementDateTime" in self.document.metadata:
            date = datetime.datetime.fromisoformat(
                self.document.metadata["statementDateTime"]
            )
        elif "creationDate" in self.document.metadata:
            date = datetime.date.fromisoformat(self.document.metadata["creationDate"])

        if date is None:
            if "subject" in self.document.metadata:
                logger.error(
                    '"%s" is missing a valid date field found in metadata. Using today\'s date as fallback.',
                    self.document.metadata["subject"],
                )
            else:
                logger.error(
                    "No valid date field found in document metadata. Using today's date as fallback."
                )
            date = datetime.date.today()

        logger.debug("PostboxItem.date() for document %s ended with %s", self.id, date)
        return date.strftime("%Y-%m-%d")


class PostBox:
    """Class for handling the DKB postbox."""

    BASE_URL = "https://banking.dkb.de/api/documentstorage/"

    # pylint: disable=w0621
    def __init__(self, client: requests.Session):
        self.client = client

    def fetch_items(self) -> Dict[str, PostboxItem]:
        """Fetches all items from the postbox and merges document and message data."""
        logger.debug("PostBox.fetch_items(): Fetching messages")

        def __fix_link_url(url: str) -> str:
            # print(f'old: {url}')
            return url.replace(
                "https://api.developer.dkb.de/documentstorage/", PostBox.BASE_URL
            )

        response = self.client.get(PostBox.BASE_URL + "/messages")
        response.raise_for_status()
        messages = response.json()

        logger.debug("PostBox.fetch_items(): Fetching documents")
        response = self.client.get(PostBox.BASE_URL + "/documents?page%5Blimit%5D=1000")
        response.raise_for_status()
        documents = response.json()

        if messages and documents:
            # Merge raw messages and documents from JSON API (left join with documents as base).
            items = {
                doc["id"]: PostboxItem(
                    id=doc["id"],
                    document=Document(
                        **doc.get("attributes", {}),
                        link=__fix_link_url(doc["links"]["self"]),
                    ),
                    message=None,
                )
                for doc in documents.get("data", [])
            }

            # Add matching message data
            for msg in messages.get("data", []):
                msg_id = msg["id"]
                if msg_id in items:
                    items[msg_id].message = Message(
                        **msg.get("attributes", {}),
                        link=__fix_link_url(msg["links"]["self"]),
                    )

            return items
        raise DKBRoboError("Could not fetch messages/documents.")
