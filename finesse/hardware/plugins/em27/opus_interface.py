"""Module containing code for sending commands to the OPUS program for the EM27.

Communication is based on a protocol using HTTP and HTML.

The OPUS program must be running on the computer at OPUS_IP for the commands to work.
Note that this is a separate machine from the EM27!
"""
import logging

from bs4 import BeautifulSoup
from PySide6.QtCore import Slot
from PySide6.QtNetwork import QNetworkReply

from finesse.config import OPUS_IP
from finesse.em27_info import EM27Status
from finesse.hardware.http_requester import HTTPRequester
from finesse.hardware.plugins.em27.opus_interface_base import (
    OPUSError,
    OPUSInterfaceBase,
)

STATUS_FILENAME = "stat.htm"
COMMAND_FILENAME = "cmd.htm"


def parse_response(response: str) -> tuple[EM27Status, str]:
    """Parse EM27's HTML response."""
    status: EM27Status | None = None
    text: str | None = None
    errcode: int | None = None
    errtext: str = ""
    soup = BeautifulSoup(response, "html.parser")
    for td in soup.find_all("td"):
        if "id" not in td.attrs:
            continue

        id = td.attrs["id"]
        data = td.contents[0] if td.contents else ""
        if id == "STATUS":
            status = EM27Status(int(data))
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
    if errcode is not None:
        raise OPUSError.from_response(errcode, errtext)

    return status, text


class OPUSInterface(OPUSInterfaceBase, description="OPUS spectrometer"):
    """Interface for communicating with the OPUS program.

    HTTP requests are handled on a background thread.
    """

    def __init__(self) -> None:
        """Create a new OPUSInterface."""
        super().__init__()
        self._requester = HTTPRequester()

    @Slot()
    def _on_reply_received(self, reply: QNetworkReply) -> tuple[EM27Status, str]:
        """Handle received HTTP reply."""
        if reply.error() != QNetworkReply.NetworkError.NoError:
            raise OPUSError(f"Network error: {reply.errorString()}")

        response = reply.readAll().data().decode()
        status, text = parse_response(response)
        return status, text

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
        self._requester.make_request(
            f"http://{OPUS_IP}/opusrs/{filename}",
            self.pubsub_broadcast(
                self._on_reply_received, f"response.{command}", "status", "text"
            ),
        )
