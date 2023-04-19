"""Module containing code for sending commands to the OPUS program for the EM27.

Communication is based on a protocol using HTTP and HTML.

The OPUS program must be running on the computer at OPUS_IP for the commands to work.
Note that this is a separate machine from the EM27!
"""
import logging
from functools import partial
from typing import Optional

from bs4 import BeautifulSoup
from pubsub import pub
from PySide6.QtCore import Slot
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from ...config import OPUS_IP
from .opus_interface_base import OPUSInterfaceBase

STATUS_FILENAME = "stat.htm"
COMMAND_FILENAME = "cmd.htm"


class OPUSError(Exception):
    """Indicates that an error occurred while communicating with the OPUS program."""


def parse_response(response: str) -> tuple[int, str, Optional[tuple[int, str]]]:
    """Parse EM27's HTML response."""
    status: Optional[int] = None
    text: Optional[str] = None
    errcode: Optional[int] = None
    errtext: str = ""
    soup = BeautifulSoup(response, "html.parser")
    for td in soup.find_all("td"):
        if "id" not in td.attrs:
            continue

        id = td.attrs["id"]
        data = td.contents[0] if td.contents else ""
        if id == "STATUS":
            status = int(data)
        elif id == "TEXT":
            text = data
        elif id == "ERRCODE":
            errcode = int(data)
        elif id == "ERRTEXT":
            errtext = data
        else:
            logging.warning(f"Received unknown ID: {id}")

    if status is None or text is None:
        raise OPUSError("Required tags not found")
    error = None if errcode is None else (errcode, errtext)

    return status, text, error


class OPUSInterface(OPUSInterfaceBase):
    """Interface for communicating with the OPUS program.

    HTTP requests are handled on a background thread.
    """

    def __init__(self, timeout: float = 3.0) -> None:
        """Create a new OPUSInterface.

        Args:
            timeout: Amount of time before request times out (seconds)
        """
        super().__init__()

        self._manager = QNetworkAccessManager()
        self._timeout = timeout

    @Slot()
    def _on_reply_received(self, reply: QNetworkReply, command: str) -> None:
        """Handle received HTTP reply."""
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                raise OPUSError(f"Network error: {reply.errorString()}")

            response = reply.readAll().data().decode()
            status, text, error = parse_response(response)
        except Exception as error:
            self.error_occurred(error)
        else:
            pub.sendMessage(
                f"opus.response.{command}", status=status, text=text, error=error
            )

    def request_command(self, command: str) -> None:
        """Request that OPUS run the specified command.

        Note that we treat "status" as a command, even though it requires a different
        URL to access.

        Args:
            command: Name of command to run
        """
        filename = (
            STATUS_FILENAME
            if command == "status"
            else f"{COMMAND_FILENAME}?opusrs{command}"
        )

        # Make HTTP request in background
        request = QNetworkRequest(f"http://{OPUS_IP}/opusrs/{filename}")
        request.setTransferTimeout(round(1000 * self._timeout))
        reply = self._manager.get(request)
        reply.finished.connect(partial(self._on_reply_received, reply, command))
