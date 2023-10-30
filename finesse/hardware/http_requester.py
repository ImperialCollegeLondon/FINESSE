"""A simple wrapper for Qt's HTTP network request code."""
from collections.abc import Callable
from functools import partial
from typing import Any

from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from finesse.config import DEFAULT_HTTP_TIMEOUT


class HTTPRequester:
    """A simple wrapper for Qt's HTTP network request code."""

    def __init__(self, timeout: float = DEFAULT_HTTP_TIMEOUT) -> None:
        """Create a new HTTPRequester.

        This does not make any connection.
        """
        self._timeout = timeout
        self._manager = QNetworkAccessManager()

    def make_request(self, url: str, callback: Callable[[QNetworkReply], Any]) -> None:
        """Make a new HTTP request.

        Args:
            url: The URL to connect to
            callback: Function to be invoked when the request finishes
        """
        # Make HTTP request in background
        request = QNetworkRequest(url)
        request.setTransferTimeout(round(1000 * self._timeout))
        reply = self._manager.get(request)
        reply.finished.connect(partial(callback, reply))
