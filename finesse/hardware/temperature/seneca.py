"""This module provides an interface to Seneca temperature readers."""
from decimal import Decimal

from serial import Serial, SerialException

from .temperature_monitor_base import TemperatureMonitorBase


def check_data(data: bytes) -> None:
    """Perform message integrity checks.

    Args:
        data: the message to check

    Raises:
        SenecaError: Malformed message received from device
    """


def calculate_bcc(data: bytes) -> None:
    """Calculate block check character.

    Args:
        data: the message to check

    Returns:
        bcc: block check character
    """


def parse_data(data: bytes) -> None:
    """Parse temperature data read from the Seneca.

    The sequence of bytes is translated into a list of ASCII strings
    representing each of the temperatures, and finally into floats.

    Returns:
        vals: A list of Decimals containing the temperature values recorded
              by the DP9800 device.
        sysflag: string representation of the system flag bitmask
    """


class SenecaError(Exception):
    """Indicates that an error occurred while communicating with the device."""


class Seneca(TemperatureMonitorBase):
    """An interface for Seneca temperature readers.

    The manual for this device is available at:
    [Link here]
    """

    def __init__(self, serial: Serial) -> None:
        """Create a new Seneca from an existing serial device.

        Args:
            serial: Serial device
        """
        self.serial = serial
        super().__init__()

    def close(self) -> None:
        """Close the connection to the device."""
        self.serial.close()

    def read(self) -> bytes:
        """Read temperature data from the Seneca.

        Returns:
            data: the sequence of bytes read from the device

        Raises:
            SenecaError: Malformed message received from device
        """
        try:
            data = self.serial.read(size=21)
        except SerialException as e:
            raise SenecaError(e)

        # require at least 4 bytes else checks will fail
        min_length = 21
        if len(data) < min_length:
            raise SenecaError("Insufficient data read from device")

        return data

    def request_read(self) -> None:
        """Write a message to the Seneca to prepare for a read operation.

        Raises:
            SenecaError: Error writing to the device
        """
        try:
            self.serial.write(bytearray([1, 3, 0, 2, 0, 8, 229, 204]))
        except Exception as e:
            raise SenecaError(e)

    def get_temperatures(self) -> list[Decimal]:
        """Get the current temperatures."""
        self.request_read()
        self.read()
        # temperatures, _ = parse_data(data)
        return [Decimal(1)]
