"""Refresher to hold open a session and refresh it periodically.

This is useful when experimenting in a REPL.

For a one-time refresh, just call the refresh method.

>>> SessionRefresher().refresh()

For a continuous refresh, use the start/stop methods.

>>> refresher = SessionRefresher()
>>> refresher.start()
>>> # ...
>>> refresher.stop()

Restarting of the thread is not supported. (Create a new instance instead.)
"""

import logging
import threading
import requests


class SessionRefresher:
    """ agent to periodically refresh the session """
    client: requests.Session
    refresh_url: str
    polling_period: float
    _stop_event: threading.Event
    _thread: threading.Thread

    def __init__(
            self,
            client: requests.Session,
            refresh_url: str = "https://banking.dkb.de/api/refresh",
            polling_period: float = 4 * 60,
        ) -> None:
        self.client: requests.Session = client
        self.refresh_url: str = refresh_url
        self.polling_period: float = polling_period
        self._stop_event: threading.Event = threading.Event()
        self._thread: threading.Thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        while not self._stop_event.wait(self.polling_period):
            self.refresh()

    def refresh(self) -> None:
        try:
            response = self.client.post(self.refresh_url)
            response.raise_for_status()
            logging.debug(f"Successfully refreshed session: {response.status_code}")
        except requests.RequestException as e:
            logging.error(f"Error occurred while refreshing session: {e}")

    def start(self) -> None:
        if not self._thread.is_alive():
            self._stop_event.clear()
            self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join()
