"""Module containing code for sending commands to the OPUS program for the EM27.

Communication is based on a protocol using HTTP and HTML.

The OPUS program must be running on the computer at OPUS_IP for the commands to work.
Note that this is a separate machine from the EM27!
"""
from typing import Optional, cast

import requests
from bs4 import BeautifulSoup
from pubsub import pub
from PySide6.QtCore import QObject, QThread, Signal, Slot

from ..config import OPUS_IP

STATUS_FILENAME = "stat.htm"
COMMAND_FILENAME = "cmd.htm"


class OPUSRequester(QThread):
    """Interface for making HTTP requests on a background thread."""

    request_complete = Signal(requests.Request, str)

    def __init__(self) -> None:
        """Create a new OPUSRequester."""
        super().__init__()
        self.moveToThread(self)

    @Slot()
    def make_request(self, filename: str, topic: str):
        """Make a request to the OPUS program.

        Args:
            filename: The final part of the path on the HTTP server
            topic: The topic on which to publish the response
        """
        url = f"http://{OPUS_IP}/opusrs/{filename}"
        response = requests.get(url)
        self.request_complete.emit(response, topic)


class OPUSInterface(QObject):
    """Interface for communicating with the OPUS program.

    HTTP requests are handled on a background thread.
    """

    submit_request = Signal(str, str)
    """Signal indicating that an HTTP request should be made."""

    def __init__(self) -> None:
        """Create a new OPUSInterface."""
        super().__init__()

        self.requester = OPUSRequester()
        """For running HTTP requests in the background."""
        self.requester.request_complete.connect(self._parse_response)

        # Set up a signal for communicating between threads
        self.submit_request.connect(self.requester.make_request)

        # Subscribe to requests coming from the GUI
        pub.subscribe(self.request_status, "opus.status.request")
        pub.subscribe(self.request_command, "opus.command.request")

        # Start processing requests
        self.requester.start()

    def __del__(self) -> None:
        """Stop the background request thread."""
        self.requester.quit()
        self.requester.wait()

    def _parse_response(self, response: requests.Response, topic: str) -> None:
        assert response.status_code == 200

        status: Optional[int] = None
        text = ""
        errcode: Optional[int] = None
        errtext = ""
        soup = BeautifulSoup(response.content, "html.parser")
        for td in soup.find_all("td"):
            if "id" not in td.attrs:
                continue

            id = td.attrs["id"]
            data = td.contents[0]
            if id == "STATUS":
                status = int(data)
            elif id == "TEXT":
                text = data
            elif id == "ERRCODE":
                errcode = int(data)
            elif id == "ERRTEXT":
                errtext = data

        if status is None or not text:
            raise ValueError("Required tags not found")
        error = None if errcode is None else (errcode, errtext)

        pub.sendMessage(
            topic, url=response.url, status=cast(int, status), text=text, error=error
        )

    def request_status(self) -> None:
        """Request an update on the device's status."""
        self.submit_request.emit(STATUS_FILENAME, "opus.status.response")

    def request_command(self, command: str) -> None:
        """Request that OPUS run the specified command."""
        self.submit_request.emit(
            f"{COMMAND_FILENAME}?opusrs{command}", "opus.command.response"
        )
