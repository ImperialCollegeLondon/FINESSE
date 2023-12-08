"""Module containing code for sending commands to the OPUS program for the EM27.

Communication is based on a protocol using HTTP and HTML.

The OPUS program must be running on the computer at OPUS_IP for the commands to work.
Note that this is a separate machine from the EM27!
"""
import logging

from bs4 import BeautifulSoup
from PySide6.QtCore import QTimer, Slot
from PySide6.QtNetwork import QNetworkReply

from finesse.config import OPUS_IP, OPUS_POLLING_INTERVAL
from finesse.hardware.http_requester import HTTPRequester
from finesse.hardware.plugins.spectrometer.opus_interface_base import (
    OPUSError,
    OPUSInterfaceBase,
)
from finesse.spectrometer_status import SpectrometerStatus

STATUS_FILENAME = "stat.htm"
COMMAND_FILENAME = "cmd.htm"


def parse_response(response: str) -> SpectrometerStatus:
    """Parse OPUS's HTML response."""
    status: SpectrometerStatus | None = None
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
            status = SpectrometerStatus(int(data))
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

    logging.info(f"OPUS response ({status.value}): {text}")

    return status


class OPUSInterface(OPUSInterfaceBase, description="OPUS spectrometer"):
    """Interface for communicating with the OPUS program.

    HTTP requests are handled on a background thread.
    """

    def __init__(self) -> None:
        """Create a new OPUSInterface."""
        super().__init__()
        self._requester = HTTPRequester()
        self._status = SpectrometerStatus.UNDEFINED

        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._request_status)
        self._status_timer.setInterval(int(OPUS_POLLING_INTERVAL * 1000))
        self._status_timer.setSingleShot(True)

        self._request_status()

    def close(self) -> None:
        """Close the device."""
        self._status_timer.stop()
        super().close()

    @Slot()
    def _on_reply_received(self, reply: QNetworkReply) -> None:
        """Handle received HTTP reply."""
        if reply.error() != QNetworkReply.NetworkError.NoError:
            raise OPUSError(f"Network error: {reply.errorString()}")

        # Parse the received message
        response = reply.readAll().data().decode()
        new_status = parse_response(response)

        # If the status has changed, notify listeners
        if new_status != self._status:
            self._status = new_status
            self.send_status_message(new_status)

        # Poll the status again after a delay
        self._status_timer.start()

    def _make_request(self, filename: str) -> None:
        """Make an HTTP request in the background."""
        self._requester.make_request(
            f"http://{OPUS_IP}/opusrs/{filename}",
            self.pubsub_errors(self._on_reply_received),
        )

    def _request_status(self) -> None:
        """Request the current status from OPUS."""
        self._make_request(STATUS_FILENAME)

    def request_command(self, command: str) -> None:
        """Request that OPUS run the specified command.

        Args:
            command: Name of command to run
        """
        self._make_request(f"{COMMAND_FILENAME}?opusrs{command}")
