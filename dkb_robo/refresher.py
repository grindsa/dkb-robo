"""Refresher to hold open a session and refresh it periodically.

This is useful when experimenting in a REPL.

For a one-time refresh, just call the refresh method.

>>> BankingSessionRefresher().refresh()

For a continuous refresh, use the start/stop methods.

>>> refresher = BankingSessionRefresher()
>>> refresher.start()
>>> # ...
>>> refresher.stop()

Restarting of the thread is not supported. (Create a new instance instead.)
"""

import logging
import threading
import requests
from typing import Optional


class SessionRefresher:
    """ agent to periodically refresh a session """
    # Client to use in order to persist cookies
    client: requests.Session

    # URL to refresh
    refresh_url: str

    # GET/POST
    method: str

    # How long to wait between refreshes
    polling_period_seconds: float

    # Event that can be triggered to stop the refresh loop
    _stop_event: threading.Event

    # Thread in which the refresh loop is running
    _thread: threading.Thread

    # If this text is found in the response, then the session refresh failed.
    # This is useful in case the status code is 200 in the case of a failed refresh.
    failure_text: Optional[str] = None

    # Default values for attribute initialization used by the constructor.
    # These are meant to be overridden by subclasses.
    default_polling_period: Optional[float] = None
    default_refresh_url: Optional[str] = None
    default_method: Optional[str] = None
    default_failure_text: Optional[str] = None

    logger: logging.Logger

    def __init__(
            self,
            client: requests.Session,
            refresh_url: Optional[str] = None,
            method: Optional[str] = None,
            polling_period: Optional[float] = None,
            failure_text: Optional[str] = None,
            logger: Optional[logging.Logger] = None) -> None:
        self.client = client
        self.logger = logger or logging.getLogger(__name__)

        refresh_url = refresh_url or self.default_refresh_url
        if refresh_url is None:
            raise ValueError("refresh_url is required")
        self.refresh_url = refresh_url

        method = method or self.default_method
        if method is None:
            raise ValueError("method (GET/POST) is required")
        self.method = method

        polling_period = polling_period or self.default_polling_period
        if polling_period is None:
            raise ValueError("polling_period is required")
        self.polling_period_seconds = polling_period

        failure_text = failure_text or self.default_failure_text
        self.failure_text = failure_text

        self._stop_event: threading.Event = threading.Event()
        self._thread: threading.Thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        """ refresh loop to be run in a thread. """
        self.logger.debug(
            f"Starting session refresh loop for {self.refresh_url} "
            f"every {self.polling_period_seconds} seconds"
        )
        while not self._stop_event.wait(self.polling_period_seconds):
            self.refresh()
        self.logger.debug("Session refresh loop finished")

    def refresh(self) -> None:
        """ refresh the session a single time """
        try:
            response = self.client.request(self.method, self.refresh_url)
            response.raise_for_status()
            self.logger.debug(f"Successfully refreshed session: {response.status_code}")
        except requests.RequestException as e:
            self.logger.error(f"Error occurred while refreshing session: {e}")
        if self.failure_text and self.failure_text in response.text:
            self.logger.error(
                f"Session refresh failed because it contains '{self.failure_text}'"
            )

    def start(self) -> None:
        """ start the refresh loop in a thread """
        if not self._thread.is_alive():
            self._stop_event.clear()
            self._thread.start()

    def stop(self) -> None:
        """ stop the refresh loop """
        self._stop_event.set()
        self._thread.join()


class BankingSessionRefresher(SessionRefresher):
    """ agent to periodically refresh the main banking session """
    default_refresh_url: str = "https://banking.dkb.de/api/refresh"
    default_method: str = "POST"
    # Timeout is 5 minutes, so we refresh every 4 minutes
    default_polling_period: float = 4 * 60


class OldBankingSessionRefresher(SessionRefresher):
    """ agent to periodically refresh the old banking session """
    default_refresh_url: str = "https://www.ib.dkb.de/ssohl/banking/postfach"
    default_method: str = "GET"
    default_failure_text: Optional[str] = "Entdecke dein neues Banking!"
    # Timeout is 2 minutes, so we refresh every 1.5 minutes.
    default_polling_period: float = 90
