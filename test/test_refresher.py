""" unittests for refresher.py """
import sys
import unittest
from unittest.mock import Mock, patch
import requests
import threading
import logging

sys.path.insert(0, '.')
sys.path.insert(0, '..')
from dkb_robo.refresher import SessionRefresher, BankingSessionRefresher, OldBankingSessionRefresher

class TestRefresher(unittest.TestCase):
    """ test class for SessionRefresher and its subclasses """

    maxDiff = None

    def setUp(self):
        self.logger = logging.getLogger('dkb_robo')
        self.session = requests.Session()

    def test_001_session_refresher_init(self):
        """ Test initialization of SessionRefresher """
        refresher = SessionRefresher(
            client=self.session,
            refresh_url='https://example.com/refresh',
            method='GET',
            polling_period=60,
            failure_text='Session expired',
            logger=self.logger
        )
        self.assertEqual(refresher.refresh_url, 'https://example.com/refresh')
        self.assertEqual(refresher.method, 'GET')
        self.assertEqual(refresher.polling_period_seconds, 60)
        self.assertEqual(refresher.failure_text, 'Session expired')
        self.assertIs(refresher.client, self.session)
        self.assertIs(refresher.logger, self.logger)

    def test_002_refresh_success(self):
        """ Test refresh method with successful response """
        refresher = SessionRefresher(
            client=self.session,
            refresh_url='https://example.com/refresh',
            method='GET',
            polling_period=60,
            logger=self.logger
        )
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        with patch.object(self.session, 'request', return_value=mock_response) as mock_request:
            with self.assertLogs(self.logger, level='DEBUG') as cm:
                refresher.refresh()
            mock_request.assert_called_once_with('GET', 'https://example.com/refresh')
            self.assertIn('DEBUG:dkb_robo:Successfully refreshed session: 200', cm.output)

    def test_003_refresh_failure_status(self):
        """ Test refresh method with HTTP error """
        refresher = SessionRefresher(
            client=self.session,
            refresh_url='https://example.com/refresh',
            method='GET',
            polling_period=60,
            logger=self.logger
        )
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError('Internal Server Error')
        with patch.object(self.session, 'request', return_value=mock_response):
            with self.assertLogs(self.logger, level='ERROR') as cm:
                refresher.refresh()
            self.assertIn('ERROR:dkb_robo:Error occurred while refreshing session: Internal Server Error', cm.output)

    def test_004_refresh_failure_text(self):
        """ Test refresh method with failure text in response """
        refresher = SessionRefresher(
            client=self.session,
            refresh_url='https://example.com/refresh',
            method='GET',
            polling_period=60,
            failure_text='Session expired',
            logger=self.logger
        )
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.text = 'Error: Session expired.'
        with patch.object(self.session, 'request', return_value=mock_response):
            with self.assertLogs(self.logger, level='ERROR') as cm:
                refresher.refresh()
            self.assertIn("ERROR:dkb_robo:Session refresh failed because it contains 'Session expired'", cm.output)

    def test_005_start_and_stop(self):
        """ Test start and stop methods """
        refresher = SessionRefresher(
            client=self.session,
            refresh_url='https://example.com/refresh',
            method='GET',
            polling_period=0.1,
            logger=self.logger
        )
        with patch.object(refresher, 'refresh') as mock_refresh:
            refresher.start()
            self.assertTrue(refresher._thread.is_alive())
            # Allow some time for the thread to run
            threading.Event().wait(0.3)
            refresher.stop()
            self.assertFalse(refresher._thread.is_alive())
            self.assertGreaterEqual(mock_refresh.call_count, 2)

    def test_006_banking_session_refresher_defaults(self):
        """ Test BankingSessionRefresher default parameters """
        refresher = BankingSessionRefresher(client=self.session)
        self.assertEqual(refresher.refresh_url, 'https://banking.dkb.de/api/refresh')
        self.assertEqual(refresher.method, 'POST')
        self.assertEqual(refresher.polling_period_seconds, 240)
        self.assertIs(refresher.client, self.session)

    def test_007_old_banking_session_refresher_defaults(self):
        """ Test OldBankingSessionRefresher default parameters """
        refresher = OldBankingSessionRefresher(client=self.session)
        self.assertEqual(refresher.refresh_url, 'https://www.ib.dkb.de/ssohl/banking/postfach')
        self.assertEqual(refresher.method, 'GET')
        self.assertEqual(refresher.polling_period_seconds, 90)
        self.assertEqual(refresher.failure_text, 'Entdecke dein neues Banking!')
        self.assertIs(refresher.client, self.session)

    def test_008_cannot_restart_thread(self):
        """ Test that restarting the refresher thread is not supported """
        refresher = SessionRefresher(
            client=self.session,
            refresh_url='https://example.com/refresh',
            method='GET',
            polling_period=0.1,
            logger=self.logger
        )
        with patch.object(refresher, '_run'):
            refresher.start()
            refresher.stop()
            with self.assertRaises(RuntimeError):
                refresher.start()

    def test_009_refresh_loop(self):
        """ Test that _run method calls refresh periodically """
        refresher = SessionRefresher(
            client=self.session,
            refresh_url='https://example.com/refresh',
            method='GET',
            polling_period=0.1,
            logger=self.logger
        )
        with patch.object(refresher, 'refresh') as mock_refresh:
            stop_event = threading.Event()
            original_stop_event = refresher._stop_event
            refresher._stop_event = stop_event  # Override to control the loop
            with patch.object(refresher._stop_event, 'wait', side_effect=[False, False, True]):
                refresher._run()
            self.assertEqual(mock_refresh.call_count, 2)
            refresher._stop_event = original_stop_event  # Restore original stop event

    def test_010_init_missing_refresh_url(self):
        """ Test that ValueError is raised when refresh_url is missing """
        with self.assertRaises(ValueError) as context:
            SessionRefresher(
                client=self.session,
                refresh_url=None,
                method='GET',
                polling_period=60,
                logger=self.logger
            )
        self.assertEqual(str(context.exception), "refresh_url is required")

    def test_011_init_missing_method(self):
        """ Test that ValueError is raised when method is missing """
        with self.assertRaises(ValueError) as context:
            SessionRefresher(
                client=self.session,
                refresh_url='https://example.com/refresh',
                method=None,
                polling_period=60,
                logger=self.logger
            )
        self.assertEqual(str(context.exception), "method (GET/POST) is required")

    def test_012_init_missing_polling_period(self):
        """ Test that ValueError is raised when polling_period is missing """
        with self.assertRaises(ValueError) as context:
            SessionRefresher(
                client=self.session,
                refresh_url='https://example.com/refresh',
                method='GET',
                polling_period=None,
                logger=self.logger
            )
        self.assertEqual(str(context.exception), "polling_period is required")

    def test_013_init_with_defaults(self):
        """ Test that defaults in subclasses are used when parameters are missing """
        # Testing BankingSessionRefresher without providing parameters
        refresher = BankingSessionRefresher(client=self.session)
        self.assertEqual(refresher.refresh_url, 'https://banking.dkb.de/api/refresh')
        self.assertEqual(refresher.method, 'POST')
        self.assertEqual(refresher.polling_period_seconds, 240)

        # Now providing parameters to override defaults
        refresher = BankingSessionRefresher(
            client=self.session,
            refresh_url='https://custom.com/refresh',
            method='GET',
            polling_period=120
        )
        self.assertEqual(refresher.refresh_url, 'https://custom.com/refresh')
        self.assertEqual(refresher.method, 'GET')
        self.assertEqual(refresher.polling_period_seconds, 120)

if __name__ == '__main__':
    unittest.main()
