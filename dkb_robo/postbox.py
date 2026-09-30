"""Module for handling the DKB postbox."""

import datetime
import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union
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

    def _metadata(self) -> Dict[str, Any]:
        """Return document metadata as dictionary."""
        if isinstance(self.document.metadata, dict):
            return self.document.metadata
        return {}

    def _has_metadata_key(self, key: str) -> bool:
        """Return whether metadata contains key."""
        return key in self._metadata()

    def _metadata_value(self, key: str) -> Any:
        """Return metadata value for key, or None if absent."""
        return self._metadata().get(key)

    def _response_detail(self, response: requests.Response) -> str:
        """Return short response text detail for error reporting."""
        response_text = response.text if response.text else ""
        return f"; response={response_text[:200]}" if response_text else ""

    def _expected_filename(self) -> str:
        """Return raw filename before sanitization."""
        filename = self.document.fileName
        # Depot related files don't have meaningful filenames but only contain the document id.
        if self._has_metadata_key("dwpDocumentId") and self._has_metadata_key(
            "subject"
        ):
            filename = self.subject() or self.document.fileName

        if (
            self.document.contentType == "application/pdf"
            and filename is not None
            and not filename.endswith("pdf")
        ):
            filename = f"{filename}.pdf"
        return filename or ""

    def _parse_metadata_date(self) -> Optional[Union[datetime.date, datetime.datetime]]:
        """Parse date from known metadata fields."""
        if self._has_metadata_key("statementDate"):
            try:
                return datetime.date.fromisoformat(
                    self._metadata_value("statementDate")
                )
            except (TypeError, ValueError):
                return None

        if self._has_metadata_key("statementDateTime"):
            try:
                return datetime.datetime.fromisoformat(
                    self._metadata_value("statementDateTime")
                )
            except (TypeError, ValueError):
                return None

        if self._has_metadata_key("creationDate"):
            try:
                return datetime.date.fromisoformat(self._metadata_value("creationDate"))
            except (TypeError, ValueError):
                return None

        return None

    def _compute_checksum(self, target_file: Path, checksum: str) -> str:
        """Compute checksum digest for file based on checksum length."""
        with target_file.open("rb") as file:
            content = file.read()

        if len(checksum) == 32:
            return hashlib.md5(content).hexdigest()
        if len(checksum) == 128:
            return hashlib.sha512(content).hexdigest()
        raise DKBRoboError(
            f"Unsupported checksum length: {len(checksum)}, {checksum}"
        )

    def _checksum_mismatch_path(self, target_file: Path) -> Path:
        """Return renamed path for checksum mismatch."""
        return target_file.with_name(target_file.name + ".checksum_mismatch")

    def mark_read(
        self, client: requests.Session, read: bool, timeout: float = 10.0
    ):
        """Marks the document as read or unread."""
        logger.debug("PostboxItem.mark_read(): set document %s to %s", self.id, read)
        try:
            resp = client.patch(
                self.message.link,
                json={"data": {"attributes": {"read": read}, "type": "message"}},
                headers={"Accept": JSON_CONTENT_TYPE, "Content-type": JSON_CONTENT_TYPE},
                timeout=timeout,
            )
        except requests.RequestException as err:
            raise DKBRoboError(
                f"postbox mark_read failed for {self.id}: request failed: {err}"
            ) from err

        try:
            resp.raise_for_status()
        except requests.HTTPError as err:
            raise DKBRoboError(
                f"postbox mark_read failed for {self.id}: http status code is {resp.status_code}{self._response_detail(resp)}"
            ) from err

    def check_checksum(self, target_file: Path):
        """Validate checksum and rename file on mismatch."""
        logger.debug("PostboxItem.check_checksum(): %s", self.id)
        computed_checksum = self._compute_checksum(target_file, self.document.checksum)

        if computed_checksum != self.document.checksum:
            logger.warning(
                "Checksum mismatch for %s: %s != %s. Renaming file.",
                target_file,
                computed_checksum,
                self.document.checksum,
            )
            mismatch_path = self._checksum_mismatch_path(target_file)
            if not mismatch_path.exists():
                target_file.rename(mismatch_path)
            else:
                logger.warning(
                    "File %s already exists. Not renaming.", mismatch_path
                )

    # Backward-compatible alias for typo in older callers.
    def check_checsum(self, target_file: Path):
        self.check_checksum(target_file)

    def download(
        self,
        client: requests.Session,
        target_file: Path,
        overwrite: bool = False,
        timeout: float = 10.0,
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
            try:
                resp = client.get(
                    self.document.link,
                    headers={"Accept": self.document.contentType},
                    timeout=timeout,
                )
            except requests.RequestException as err:
                raise DKBRoboError(
                    f"postbox download failed for {self.id}: request failed: {err}"
                ) from err

            try:
                resp.raise_for_status()
            except requests.HTTPError as err:
                raise DKBRoboError(
                    f"postbox download failed for {self.id}: http status code is {resp.status_code}{self._response_detail(resp)}"
                ) from err

            # create directories if necessary
            target_file.parent.mkdir(parents=True, exist_ok=True)

            with target_file.open("wb") as file:
                file.write(resp.content)

            if self.document.checksum:
                # compare checksums of file with checksum from document metadata
                self.check_checksum(target_file)

            return resp.status_code
        return False

    def filename(self) -> str:
        """Returns a sanitized filename based on the document metadata."""
        logger.debug(
            "PostboxItem.filename(): Generating filename for document %s", self.id
        )

        fname = get_valid_filename(self._expected_filename())
        logger.debug("PostboxItem.filename() for %s ended with %s", self.id, fname)
        return fname

    def subject(self) -> str:
        """Returns the subject of the message."""
        message_subject = self.message.subject if self.message else None
        if self._has_metadata_key("subject"):
            return self._metadata_value("subject")
        return message_subject

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
        if self._has_metadata_key("depotNumber"):
            account = self._metadata_value("depotNumber")
        elif self._has_metadata_key("cardId"):
            card_id = self._metadata_value("cardId")
            account = card_lookup.get(
                card_id, card_id
            )
        elif self._has_metadata_key("iban"):
            account = self._metadata_value("iban")

        logger.debug(
            "PostboxItem.account() for document %s ended with %s", self.id, account
        )
        return account

    def date(self) -> str:
        """Returns the date of the document based on the metadata."""
        logger.debug("PostboxItem.date() for document %s", self.id)
        date = self._parse_metadata_date()

        if date is None:
            if self._has_metadata_key("subject"):
                logger.error(
                    '"%s" is missing a valid date field found in metadata. Using today\'s date as fallback.',
                    self._metadata_value("subject"),
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
    def __init__(self, client: requests.Session, timeout: float = 10.0):
        self.client = client
        self.timeout = timeout

    def _fetch_json(self, url: str) -> Dict[str, Any]:
        """Fetch JSON payload from an endpoint with robust error handling."""
        try:
            response = self.client.get(url, timeout=self.timeout)
        except requests.RequestException as err:
            raise DKBRoboError(f"postbox fetch failed for {url}: {err}") from err

        try:
            response.raise_for_status()
        except requests.HTTPError as err:
            response_text = response.text if response.text else ""
            response_detail = f"; response={response_text[:200]}" if response_text else ""
            raise DKBRoboError(
                f"postbox fetch failed for {url}: http status code is {response.status_code}{response_detail}"
            ) from err

        try:
            payload = response.json()
        except ValueError as err:
            raise DKBRoboError(f"postbox fetch failed for {url}: invalid json") from err

        if not isinstance(payload, dict):
            raise DKBRoboError(
                f"postbox fetch failed for {url}: invalid payload type {type(payload).__name__}"
            )

        return payload

    def _fix_link_url(self, url: str) -> str:
        """Normalize documentstorage API links to base URL."""
        if not isinstance(url, str):
            return ""
        return url.replace("https://api.dkb.de/documentstorage/", PostBox.BASE_URL)

    def _payload_data_list(self, payload: Dict[str, Any]) -> list:
        """Return payload data list or an empty list for malformed payloads."""
        data = payload.get("data", [])
        return data if isinstance(data, list) else []

    def _build_items_from_documents(
        self, documents_payload: Dict[str, Any]
    ) -> Dict[str, PostboxItem]:
        """Create postbox items from documents payload."""
        items: Dict[str, PostboxItem] = {}
        for doc in self._payload_data_list(documents_payload):
            if not isinstance(doc, dict):
                continue

            doc_id = doc.get("id")
            links = doc.get("links") if isinstance(doc.get("links"), dict) else {}
            attributes = (
                doc.get("attributes") if isinstance(doc.get("attributes"), dict) else {}
            )
            link = self._fix_link_url(links.get("self")) if links else ""
            if not doc_id or not link:
                continue

            items[doc_id] = PostboxItem(
                id=doc_id,
                document=Document(**attributes, link=link),
                message=None,
            )
        return items

    def _merge_messages(
        self, items: Dict[str, PostboxItem], messages_payload: Dict[str, Any]
    ) -> None:
        """Merge message payload data into existing item map."""
        for msg in self._payload_data_list(messages_payload):
            if not isinstance(msg, dict):
                continue

            msg_id = msg.get("id")
            if msg_id not in items:
                continue

            links = msg.get("links") if isinstance(msg.get("links"), dict) else {}
            attributes = (
                msg.get("attributes") if isinstance(msg.get("attributes"), dict) else {}
            )
            link = self._fix_link_url(links.get("self")) if links else ""
            if not link:
                continue

            items[msg_id].message = Message(**attributes, link=link)

    def fetch_items(self) -> Dict[str, PostboxItem]:
        """Fetches all items from the postbox and merges document and message data."""
        logger.debug("PostBox.fetch_items(): Fetching messages")

        messages = self._fetch_json(PostBox.BASE_URL + "/messages")

        logger.debug("PostBox.fetch_items(): Fetching documents")
        documents = self._fetch_json(PostBox.BASE_URL + "/documents?page%5Blimit%5D=1000")

        if not (messages and documents):
            raise DKBRoboError("Could not fetch messages/documents.")

        items = self._build_items_from_documents(documents)
        self._merge_messages(items, messages)
        return items
