"""Tests for the postbox module."""
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import date
import requests
import logging

sys.path.insert(0, ".")
sys.path.insert(0, "..")
from dkb_robo.utilities import DKBRoboError
from dkb_robo.postbox import PostboxItem, PostBox, Document, Message


class TestPostboxItem(unittest.TestCase):
    """Tests for the PostboxItem class."""

    def setUp(self):
        self.document = Document(
            creationDate="2023-01-01",
            expirationDate="2023-12-31",
            retentionPeriod="9999-12-31",
            contentType="application/pdf",
            checksum="9473fdd0d880a43c21b7778d34872157",
            fileName="test_document",
            metadata={"statementDate": "2023-01-01"},
            owner="owner",
            link="http://example.com/document",
        )
        self.message = Message(
            archived=False,
            read=False,
            subject="Test Subject",
            documentType="bankAccountStatement",
            creationDate="2023-01-01",
            link="http://example.com/message",
        )
        self.postbox_item = PostboxItem(
            id="1",
            document=self.document,
            message=self.message,
        )

    @patch("requests.Session")
    def test_001_mark_read(self, mock_session):
        """Test that the mark_read method correctly marks a document as read or unread."""
        mock_client = mock_session.return_value
        mock_client.patch.return_value.status_code = 200
        self.postbox_item.mark_read(mock_client, True)
        mock_client.patch.assert_called_once_with(
            self.message.link,
            json={"data": {"attributes": {"read": True}, "type": "message"}},
            headers={
                "Accept": "application/vnd.api+json",
                "Content-type": "application/vnd.api+json",
            },
        )

    @patch("requests.Session")
    def test_002_mark_read_failed(self, mock_session):
        """Test that the mark_read method raises an exception if the request fails."""
        mock_client = mock_session.return_value
        mock_client.patch.return_value.raise_for_status.side_effect = (
            requests.HTTPError()
        )
        with self.assertRaises(requests.HTTPError):
            self.postbox_item.mark_read(mock_client, True)

    @patch("requests.Session")
    def test_003_download(self, mock_session):
        """Test that the download method correctly downloads a document and saves it to the specified file path."""
        mock_client = mock_session.return_value
        mock_client.get.return_value.status_code = 200
        mock_client.get.return_value.content = b"test content"
        target_file = Path(tempfile.gettempdir()) / "test_001_document.pdf"
        result = self.postbox_item.download(mock_client, target_file, overwrite=True)
        self.assertTrue(result)
        self.assertTrue(target_file.exists())
        target_file.unlink()  # Remove the downloaded test file

    @patch("requests.Session")
    def test_004_download_existing_file(self, mock_session):
        """Test that the download method does not overwrite an existing file if overwrite is False."""
        mock_client = mock_session.return_value
        target_file = Path(tempfile.gettempdir()) / "existing.pdf"
        target_file.touch()
        result = self.postbox_item.download(mock_client, target_file)
        self.assertFalse(result)
        target_file.unlink()

    @patch("requests.Session")
    def test_005_download_checksum_mismatch(self, mock_session):
        """Test that the download method renames the downloaded file if the checksum of the downloaded file does not match."""
        mock_client = mock_session.return_value
        mock_client.get.return_value.status_code = 200
        mock_client.get.return_value.content = b"wrong test content"
        target_file = Path(tempfile.gettempdir()) / "test_document.pdf"
        result = self.postbox_item.download(mock_client, target_file, overwrite=True)
        self.assertTrue(result)
        self.assertFalse(target_file.exists())
        mismatched_file = target_file.with_name(target_file.name + ".checksum_mismatch")
        self.assertTrue(mismatched_file.exists())
        mismatched_file.unlink()  # Remove the downloaded test file

    @patch("pathlib.Path.exists")
    @patch("requests.Session")
    def test_006_download_file_exists_no_overwrite(self, mock_session, mock_exists):
        """Test that the download method renames the downloaded file if the checksum of the downloaded file does not match."""
        mock_client = mock_session.return_value
        mock_client.get.return_value.status_code = 200
        mock_client.get.return_value.content = b"wrong test content"
        target_file = Path("document.pdf")
        mock_exists.side_effect = [False, True, True]
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            result = self.postbox_item.download(
                mock_client, target_file, overwrite=True
            )
        self.assertIn(
            "WARNING:dkb_robo.postbox:File document.pdf.checksum_mismatch already exists. Not renaming.",
            lcm.output,
        )
        self.assertTrue(result)
        target_file.unlink()  # Remove the downloaded test file

    def test_007_filename(self):
        """Test that the filename method returns the correct filename for the postbox item."""
        filename = self.postbox_item.filename()
        self.assertEqual(filename, "test_document.pdf")

    def test_008_category(self):
        """Test that the category method returns the correct category for the postbox item."""
        category = self.postbox_item.category()
        self.assertEqual(category, "Kontoauszüge")

    def test_009_account(self):
        """Test that the account method returns the correct account for the postbox item."""
        account = self.postbox_item.account()
        self.assertIsNone(account)

    def test_010_date(self):
        """Test that the date method returns the correct date for the postbox item."""
        date = self.postbox_item.date()
        self.assertEqual(date, "2023-01-01")

    def test_011_filename_with_depot_document(self):
        """Test that the filename method returns the correct filename for a depot document."""
        self.document.metadata = {"dwpDocumentId": "123", "subject": "Depot Statement"}
        filename = self.postbox_item.filename()
        self.assertEqual(filename, "Depot_Statement.pdf")

    def test_012_filename_basic(self):
        """Test basic filename return without modification"""
        self.document.fileName = "simple_document.pdf"
        self.assertEqual(self.postbox_item.filename(), "simple_document.pdf")

    def test_013_filename_adds_pdf_extension(self):
        """Test that .pdf extension is added for PDF content type"""
        self.document.fileName = "document_without_extension"
        self.document.contentType = "application/pdf"
        self.assertEqual(self.postbox_item.filename(), "document_without_extension.pdf")

    def test_014_filename_sanitization(self):
        """Test filename sanitization with special characters"""
        self.document.fileName = "Document Ümlaut & Spaces!.pdf"
        self.assertEqual(self.postbox_item.filename(), "Document_Ümlaut_Spaces.pdf")

    def test_015_filename_multiple_whitespace(self):
        """Test handling of multiple whitespaces in filename"""
        self.document.fileName = "12345.pdf"
        self.document.metadata = {
            "dwpDocumentId": "12345",
            "subject": "Depot    Statement     Q1    2023",
        }
        self.assertEqual(self.postbox_item.filename(), "Depot_Statement_Q1_2023.pdf")

    def test_016_filename_empty_subject(self):
        """Test handling of empty subject in depot documents"""
        self.document.fileName = "fallback.pdf"
        self.document.metadata = {"dwpDocumentId": "12345", "subject": ""}
        self.assertEqual(self.postbox_item.filename(), "fallback.pdf")

    def test_017_account_with_depot(self):
        """Test that the account method returns the correct account for a depot document."""
        self.document.metadata = {"depotNumber": "12345"}
        self.assertEqual(self.postbox_item.account(), "12345")

    def test_018_account_with_card(self):
        """Test that the account method returns the correct account for a credit card document."""
        self.document.metadata = {"cardId": "card123"}
        card_lookup = {"card123": "MyCard"}
        self.assertEqual(self.postbox_item.account(card_lookup), "MyCard")

    def test_019_account_with_card_failed_lookup(self):
        """Test that the account method returns the card ID if the lookup fails."""
        self.document.metadata = {"cardId": "card123"}
        card_lookup = {"card1234": "MyCard"}
        self.assertEqual(self.postbox_item.account(card_lookup), "card123")

    def test_020_account_with_iban(self):
        """Test that the account method returns the correct account for an IBAN document."""
        self.document.metadata = {"iban": "DE123"}
        self.assertEqual(self.postbox_item.account(), "DE123")

    def test_021_date_with_statement_datetime(self):
        """Test that the date method returns the correct date for a document with a statementDateTime field."""
        self.document.metadata = {"statementDateTime": "2023-01-01T12:00:00"}
        self.assertEqual(self.postbox_item.date(), "2023-01-01")

    def test_022_date_with_statement_date(self):
        """Test that the date method returns the correct date for a document with a statementDate field."""
        self.document.metadata = {"statementDate": "2023-01-01"}
        self.assertEqual(self.postbox_item.date(), "2023-01-01")

    def test_023_date_with_creation_date(self):
        """Test that the date method returns the correct date for a document with a creationDate field."""
        self.document.metadata = {"creationDate": "2023-01-01"}
        self.assertEqual(self.postbox_item.date(), "2023-01-01")

    @patch("dkb_robo.postbox.datetime.date")
    def test_024_date_invalid(self, mock_today):
        """Test that the date method raises an exception if no valid date field is found in the metadata."""
        self.document.metadata = {}
        mock_today.today.return_value = date(2025, 3, 23)
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertEqual("2025-03-23", self.postbox_item.date())
        self.assertIn(
            "ERROR:dkb_robo.postbox:No valid date field found in document metadata. Using today's date as fallback.",
            lcm.output,
        )

    @patch("dkb_robo.postbox.datetime.date")
    def test_025_date_invalid(self, mock_today):
        """Test that the date method raises an exception if no valid date field is found in the metadata."""
        self.document.metadata = {"subject": "subject"}
        mock_today.today.return_value = date(2025, 3, 23)
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertEqual("2025-03-23", self.postbox_item.date())
        self.assertIn(
            'ERROR:dkb_robo.postbox:"subject" is missing a valid date field found in metadata. Using today\'s date as fallback.',
            lcm.output,
        )

    @patch("requests.Session")
    def test_031_download_sha512_checksum(self, mock_session):
        """Test that the download method correctly handles SHA-512 checksums."""
        # Create a SHA-512 checksum (128 characters long)
        sha512_checksum = "a7f06f12bd5e99c59966c13cea8483ece69d27a3bf8d46f836e934f5c1ec0b55a7e22d14360949de102cd8e16a9f74806c9ce1597eefaa379fb40384403c7fd6"
        self.document.checksum = sha512_checksum

        # Mock the session and content
        mock_client = mock_session.return_value
        mock_client.get.return_value.status_code = 200
        content = b"test content for SHA-512 verification"
        mock_client.get.return_value.content = content

        # Create a target file
        target_file = Path(tempfile.gettempdir()) / "test_sha512_document.pdf"

        # Mock the SHA-512 hash computation
        with patch("hashlib.sha512") as mock_sha512:
            mock_sha512.return_value.hexdigest.return_value = sha512_checksum

            # Test the download
            result = self.postbox_item.download(
                mock_client, target_file, overwrite=True
            )

            # Verify the results
            self.assertTrue(result)
            self.assertTrue(target_file.exists())
            mock_sha512.assert_called_once_with(content)
        target_file.unlink()  # Remove the downloaded test file

    @patch("requests.Session")
    def test_032_download_sha512_checksum_mismatch(self, mock_session):
        """Test that the download method handles SHA-512 checksum mismatches correctly."""
        # Create a SHA-512 checksum (128 characters long)
        sha512_checksum = "a7f06f12bd5e99c59966c13cea8483ece69d27a3bf8d46f836e934f5c1ec0b55a7e22d14360949de102cd8e16a9f74806c9ce1597eefaa379fb40384403c7fd6"
        self.document.checksum = sha512_checksum

        # Mock the session and content
        mock_client = mock_session.return_value
        mock_client.get.return_value.status_code = 200
        content = b"test content that will cause a SHA-512 checksum mismatch"
        mock_client.get.return_value.content = content

        # Create a target file
        target_file = Path(tempfile.gettempdir()) / "test_sha512_mismatch.pdf"

        # Set up a different checksum to be returned by the SHA-512 hash function to simulate a mismatch
        wrong_checksum = "b8f06f12bd5e99c59966c13cea8483ece69d27a3bf8d46f836e934f5c1ec0b55a7e22d14360949de102cd8e16a9f74806c9ce1597eefaa379fb40384403c7fd7"

        with patch("hashlib.sha512") as mock_sha512:
            mock_sha512.return_value.hexdigest.return_value = wrong_checksum

            # Test the download
            result = self.postbox_item.download(
                mock_client, target_file, overwrite=True
            )

            # Verify the results
            self.assertTrue(result)
            self.assertFalse(target_file.exists())
            mismatched_file = target_file.with_name(
                target_file.name + ".checksum_mismatch"
            )
            self.assertTrue(mismatched_file.exists())
            mismatched_file.unlink()  # Remove the downloaded test file

    @patch("requests.Session")
    def test_033_download_unsupported_checksum_length(self, mock_session):
        """Test that the download method raises an error for unsupported checksum lengths."""
        # Create an unsupported checksum length (e.g., 64 characters)
        unsupported_checksum = "a" * 64
        self.document.checksum = unsupported_checksum

        # Mock the session and content
        mock_client = mock_session.return_value
        mock_client.get.return_value.status_code = 200
        mock_client.get.return_value.content = b"test content"

        # Create a target file
        target_file = Path(tempfile.gettempdir()) / "test_unsupported_checksum.pdf"

        # Test the download function and expect a DKBRoboError
        with self.assertRaises(DKBRoboError) as context:
            self.postbox_item.download(mock_client, target_file, overwrite=True)

        # Verify the error message
        self.assertIn(
            f"Unsupported checksum length: {len(unsupported_checksum)}",
            str(context.exception),
        )
        target_file.unlink()  # Remove the downloaded test file


class TestPostBox(unittest.TestCase):
    """Tests for the PostBox class."""

    def create_mocked_postbox(self, mock_client):
        """Create a PostBox instance with a mocked client."""
        mock_client.get.side_effect = [
            MagicMock(
                status_code=200,
                json=lambda: {
                    "data": [
                        {
                            "id": "11111111-1111-1111-1111-111111111111",
                            "attributes": {
                                "read": "True",
                                "archived": "False",
                                "subject": "Kreditkartenabrechnung vom 22. September 2023",
                                "documentType": "creditCardStatement",
                                "creationDate": "2023-09-26T06:57:34.803691Z",
                            },
                            "links": {
                                "self": "https://api.developer.dkb.de/messages/11111111-1111-1111-1111-111111111111"
                            },
                        }
                    ]
                },
            ),
            MagicMock(
                status_code=200,
                json=lambda: {
                    "data": [
                        {
                            "id": "11111111-1111-1111-1111-111111111111",
                            "attributes": {
                                "creationDate": "2023-09-01T01:01:03.456789Z",
                                "expirationDate": "2026-09-01",
                                "retentionPeriod": "P3Y",
                                "contentType": "application/pdf",
                                "checksum": "00000000000000000000000000000000",
                                "fileName": "Kreditkarte_XXXXXXXXXXXXXXXX_Abrechnung_20230901.pdf",
                                "metadata": {
                                    "statementAmount": "47.11",
                                    "statementDate": "2023-09-01",
                                    "subject": "Kreditkartenabrechnung vom 01. September 2023",
                                    "statementID": "_X_XXXXXX",
                                    "statementCurrency": "EUR",
                                    "portfolio": "dkb",
                                    "cardId": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                                },
                                "owner": "service-documentexchange-api",
                            },
                            "links": {
                                "self": "https://api.developer.dkb.de/documentstorage/documents/11111111-1111-1111-1111-111111111111"
                            },
                        }
                    ]
                },
            ),
        ]
        return PostBox(client=mock_client)

    @patch("requests.Session")
    def test_026_fetch_items(self, mock_session):
        """Test that the fetch_items method correctly fetches items from the postbox."""
        postbox = self.create_mocked_postbox(mock_session.return_value)
        items = postbox.fetch_items()
        self.assertIn("11111111-1111-1111-1111-111111111111", items)
        self.assertIsInstance(
            items["11111111-1111-1111-1111-111111111111"], PostboxItem
        )

    @patch("requests.Session")
    def test_027_sample(self, mock_session):
        """Test that the fetch_items method correctly fetches items from the postbox."""
        item = self.create_mocked_postbox(mock_session.return_value).fetch_items()[
            "11111111-1111-1111-1111-111111111111"
        ]

        self.assertEqual(
            item.filename(), "Kreditkarte_XXXXXXXXXXXXXXXX_Abrechnung_20230901.pdf"
        )
        self.assertEqual(item.account(), "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
        self.assertEqual(item.date(), "2023-09-01")
        self.assertEqual(item.category(), "Kreditkartenabrechnungen")

    @patch("requests.Session")
    def test_028_fetch_empty_responses(self, mock_session):
        """Test that the fetch_items method raises an exception if the responses are empty."""
        mock_client = mock_session.return_value
        mock_client.get.side_effect = [
            MagicMock(status_code=200, json=lambda: {}),
            MagicMock(status_code=200, json=lambda: {}),
        ]
        with self.assertRaises(DKBRoboError):
            PostBox(client=mock_client).fetch_items()

    @patch("requests.Session")
    def test_029_fetch_url_fixing(self, mock_session):
        """Test that the link URLs are correctly fixed."""
        postbox = self.create_mocked_postbox(mock_session.return_value)
        self.assertTrue(
            postbox.fetch_items()[
                "11111111-1111-1111-1111-111111111111"
            ].document.link.startswith(PostBox.BASE_URL)
        )

    @patch("requests.Session")
    def test_030_fetch_http_error(self, mock_session):
        """Test that the fetch_items method raises an exception if the request fails."""
        mock_client = mock_session.return_value
        mock_client.get.side_effect = requests.HTTPError()
        with self.assertRaises(requests.HTTPError):
            PostBox(client=mock_client).fetch_items()


if __name__ == "__main__":
    unittest.main()
