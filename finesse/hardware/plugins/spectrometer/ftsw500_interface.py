r"""Module containing code for sending commands to FTSW500 for the ABB spectrometer.

Communication is via TCP.

The FTSW500 program must be running on the computer at FTSW500_HOST for the commands to
work. The server always returns a response after having received a command. The response
will start with the tag "ACK" in case of success, or "NAK" otherwise, and is terminated
by the end-of-line character "\n". An answer can also contain a string value or message
after the tag, which will be preceded by "&". For example, querying whether the
instrument is currently measuring data would yield a response "ACK&true\n" or
"ACK&false\n".
"""

import logging
from socket import AF_INET, SOCK_STREAM, socket

from PySide6.QtCore import QTimer

from finesse.config import (
    FTSW500_HOST,
    FTSW500_POLLING_INTERVAL,
    FTSW500_PORT,
    FTSW500_TIMEOUT,
)
from finesse.hardware.plugins.spectrometer.ftsw500_interface_base import (
    FTSW500Error,
    FTSW500InterfaceBase,
)
from finesse.spectrometer_status import SpectrometerStatus


def _parse_response(response: str) -> str:
    """Parse FTSW500's response.

    The response should be one of:
        - ACK
        - ACK&extra argument
        - NAK&error message

    Returns:
        Argument sent with ACK or empty string

    Raises:
        FTSW500Error if NAK received or response is unexpected
    """
    command, _, args = response.partition("&")
    match command:
        case "ACK":
            return args
        case "NAK":
            raise FTSW500Error(args)
        case _:
            raise FTSW500Error(f"Unexpected response: {response}")


class FTSW500Interface(FTSW500InterfaceBase, description="FTSW500 spectrometer"):
    """Interface for communicating with the FTSW500 program."""

    def __init__(self) -> None:
        """Create a new FTSW500Interface."""
        super().__init__()

        sock = socket(AF_INET, SOCK_STREAM)
        sock.settimeout(FTSW500_TIMEOUT)
        sock.connect((FTSW500_HOST, FTSW500_PORT))
        self._socket = sock

        # Timer to poll status
        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self.pubsub_errors(self._update_status))
        self._status_timer.setInterval(int(FTSW500_POLLING_INTERVAL * 1000))
        self._status_timer.setSingleShot(True)

        # Find out what the initial status is
        self._status = SpectrometerStatus.UNDEFINED
        self._update_status()

    def is_modal_dialog_open(self) -> bool:
        """Query whether FTSW500 has a modal dialog open."""
        return self._make_request("isModalMessageDisplayed") == "true"

    def is_nonmodal_dialog_open(self) -> bool:
        """Query whether FTSW500 has a non-modal dialog open."""
        return self._make_request("isNonModalMessageDisplayed") == "true"

    def _log_modal_dialog_message(self) -> None:
        """Obtain the last modal message displayed on FTSW500 and log it."""
        if self.is_modal_dialog_open():
            msg = self._make_request("getLastModalMessageDisplayed")
            logging.info(f"FTSW500: {msg}")
            self._make_request("closeModalDialogMessage")

    def _log_nonmodal_dialog_message(self) -> None:
        """Obtain the last non-modal message displayed on FTSW500 and log it."""
        if self.is_nonmodal_dialog_open():
            msg = self._make_request("getLastNonModalMessageDisplayed")
            logging.info(f"FTSW500: {msg}")
            self._make_request("closeNonModalDialogMessage")

    def close(self) -> None:
        """Close the device."""
        self._status_timer.stop()

        if self._socket.fileno() != -1:  # check if closed already
            self._log_nonmodal_dialog_message()
            self._socket.close()

        super().close()

    def _get_status(self) -> SpectrometerStatus | None:
        """Request the current status from FTSW500.

        From the Java API documentation:

        Querying the FTSW500 state yields one of the following values:
            0: when disconnected
            1: when in the process of connecting to an instrument
            2: when acquiring data without saving it 3: when acquiring and saving data
            -1: when in an intermediate state that should normally not last for a long
                time (less than 500 ms) or when the FTSW500_SDK object is not well
                initialized

        Returns:
            Spectrometer status or None if in intermediate state
        """
        retval = self._make_request("getFTSW500State")

        try:
            status_num = int(retval)

            if status_num == -1:
                # Try again later
                return None
            if 0 <= status_num <= 3:
                return SpectrometerStatus(status_num)
        except ValueError:
            pass

        raise FTSW500Error(f"Invalid value received for status: {retval}")

    def _update_status(self) -> None:
        """Update the current status.

        The status polling timer is restarted to ensure that another status update will
        happen soon. If the status is intermediate (-1), then it is ignored and we just
        wait until the status is next requested.
        """
        new_status = self._get_status()

        # If the status is not intermediate and has changed since we last checked
        if new_status and new_status != self._status:
            self._status = new_status
            self.send_status_message(new_status)

        # Request another status update soon
        self._status_timer.start()

    def _make_request(self, command: str) -> str:
        """Request that FTSW500 run the specified command.

        Args:
            command: Name of command to run
        """
        self._socket.sendall(f"{command}\n".encode())

        # Read a single message, which should be terminated with a newline. As the
        # protocol is simple we don't have to worry about what happens if more than or
        # less than one line of text is received.
        response = self._socket.recv(1024).decode()
        if not response:
            raise FTSW500Error("Connection terminated unexpectedly")

        if not response.endswith("\n"):
            raise FTSW500Error("Response not terminated with newline")

        return _parse_response(response[:-1])

    def request_command(self, command: str) -> None:
        """Request that FTSW500 run the specified command.

        The status is requested after sending the command so that we are immediately
        notified if it has changed in response to the command (e.g. recording has
        started). Contents of dialogs in FTSW500 are saved to the program log.

        Args:
            command: Name of command to run
        """

        def internal():
            self._make_request(command)

            # Request a status update
            self._update_status()

            # Log the contents of dialogs
            self._log_nonmodal_dialog_message()
            self._log_modal_dialog_message()

        # Make the request, forwarding any errors raised to the frontend
        self.pubsub_errors(internal)()
