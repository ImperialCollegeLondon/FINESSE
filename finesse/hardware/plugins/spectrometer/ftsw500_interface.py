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


def parse_response(response: bytes) -> SpectrometerStatus | None:
    """Parse FTSW500's response.

    Querying the FTSW500 state yields one of the following values:
    0: when disconnected
    1: when in the process of connecting to an instrument
    2: when acquiring data without saving it
    3: when acquiring and saving data
    -1: when in an intermediate state that should normally not last for a long time
        (less than 500 ms) or when the FTSW500_SDK object is not well initialized

    Args:
        response: the byte sequence received from FTSW500

    Returns:
        SpectrometerStatus: the generic spectrometer device state of FTSW500
    """
    msg = response.decode()
    if msg.startswith("ACK&"):
        status = int(msg.split("&")[1])
    elif msg.startswith("NAK&"):
        raise FTSW500Error(msg.split("&")[1])
    else:  # i.e. "ACK"
        return None

    if status == -1:
        return SpectrometerStatus(1)
    elif status in (0, 1, 2, 3):
        return SpectrometerStatus(status)
    else:
        raise FTSW500Error("Unable to parse response")


class FTSW500Interface(FTSW500InterfaceBase, description="FTSW500 spectrometer"):
    """Interface for communicating with the FTSW500 program."""

    def __init__(self) -> None:
        """Create a new FTSW500Interface."""
        super().__init__()

        self._requester = socket(AF_INET, SOCK_STREAM)
        self._requester.settimeout(FTSW500_TIMEOUT)

        self._requester.connect((FTSW500_HOST, FTSW500_PORT))

        self._status = SpectrometerStatus.UNDEFINED

        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._request_status)
        self._status_timer.setInterval(int(FTSW500_POLLING_INTERVAL * 1000))
        self._status_timer.setSingleShot(True)

        self._request_status()

    def set_output_path_prefix(self, output_path_prefix: str) -> None:
        """Set the output path prefix for FTSW500 data."""
        self._requester.sendall(
            f"setOutputPathPrefixField&{output_path_prefix}\n".encode()
        )
        self._requester.recv(1024)

    def set_output_prefix(self, output_prefix: str) -> None:
        """Set the output prefix for FTSW500 data."""
        self._requester.sendall(f"setOutputPrefixOnlyField&{output_prefix}\n".encode())
        self._requester.recv(1024)

    def set_data_description(self, data_description: str) -> None:
        """Set the description for FTSW500 data."""
        self._requester.sendall(
            f"setDataDescriptionField&{data_description}\n".encode()
        )
        self._requester.recv(1024)

    def set_num_measurements(self, num_measurements: int) -> None:
        """Set the number of measurements for FTSW500 to record."""
        self._requester.sendall(
            f"setNumberMeasurementField&{num_measurements}\n".encode()
        )
        self._requester.recv(1024)

    def set_temperature(self, temperature: float) -> None:
        """Set the temperature for FTSW500 data."""
        self._requester.sendall(f"setTemperatureField&{temperature}\n".encode())
        self._requester.recv(1024)

    def is_modal_dialog_open(self) -> bool:
        """Query whether FTSW500 has a modal dialog open."""
        self._requester.sendall(b"isModalMessageDisplayed\n")
        data = self._requester.recv(1024)
        if data.decode().split("&")[1] == "true\n":
            return True
        else:
            return False

    def is_nonmodal_dialog_open(self) -> bool:
        """Query whether FTSW500 has a non-modal dialog open."""
        self._requester.sendall(b"isNonModalMessageDisplayed\n")
        data = self._requester.recv(1024)
        if data.decode().split("&")[1] == "true\n":
            return True
        else:
            return False

    def _log_modal_dialog_message(self) -> None:
        """Obtain the last modal message displayed on FTSW500 and log it."""
        if self.is_modal_dialog_open():
            self._requester.sendall(b"getLastModalMessageDisplayed\n")
            data = self._requester.recv(1024)
            logging.info(f"FTSW500: {data.decode().split('&')[1][:-1]}")
            self._requester.sendall(b"closeModalDialogMessage\n")
            self._requester.recv(1024)

    def _log_nonmodal_dialog_message(self) -> None:
        """Obtain the last non-modal message displayed on FTSW500 and log it."""
        if self.is_nonmodal_dialog_open():
            self._requester.sendall(b"getLastNonModalMessageDisplayed\n")
            data = self._requester.recv(1024)
            logging.info(f"FTSW500: {data.decode().split('&')[1][:-1]}")
            self._requester.sendall(b"closeNonModalDialogMessage\n")
            self._requester.recv(1024)

    def close_FTSW500(self) -> None:
        """Close the FTSW500 program."""
        self._requester.sendall(b"closeFTSW500\n")

    def disconnect(self) -> None:
        """Disconnect from the spectrometer."""
        self._requester.sendall(b"clickDisconnectButton\n")
        self._requester.recv(1024)

    def close(self) -> None:
        """Close the device."""
        if self._status == SpectrometerStatus.CONNECTED:
            self._log_nonmodal_dialog_message()
        self._requester.close()
        self._status_timer.stop()
        super().close()

    def _on_reply_received(self, reply: bytes) -> None:
        """Handle received reply.

        Args:
            reply: the byte sequence received from the FTSW500 program
        """
        new_status = parse_response(reply)
        if new_status is not None:
            if new_status != self._status:
                self._status = new_status
                self.send_status_message(new_status)

        self._status_timer.start()

        self._log_nonmodal_dialog_message()
        self._log_modal_dialog_message()

    def _request_status(self) -> None:
        """Request the current status from FTSW500."""
        self.request_command("getFTSW500State")

    def request_command(self, command: str) -> None:
        """Request that FTSW500 run the specified command.

        Args:
            command: Name of command to run
        """
        self._requester.sendall(f"{command}\n".encode())
        self._on_reply_received(self._requester.recv(1024))
