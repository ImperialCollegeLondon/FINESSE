"""This module provides an interface to Seneca temperature readers."""
from decimal import Decimal

import numpy
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

    def parse_data(self, data: bytes) -> list[Decimal]:
        """Parse temperature data read from the Seneca.

        The sequence of bytes is translated into a list of ASCII strings
        representing each of the temperatures, and finally into floats.

        Returns:
            vals: A list of Decimals containing the temperature values recorded
                by the Seneca device.
        """
        ints = numpy.frombuffer(data, numpy.uint16, 8, 3)
        print("ints:", ints, type(ints))

        temps = [Decimal(float(self.calc_temp(val))) for val in ints]
        print("temps:", temps, type(temps))
        return temps

    def calc_temp(self, val: numpy.float64) -> numpy.float64:
        """Calculate temp."""
        temp = (self.range * ((val / 1000) - self.min_volt)) + self.min_temp
        print("temp:", temp, type(temp))
        return temp

    def get_temperatures(self) -> list[Decimal]:
        """Get the current temperatures."""
        self.request_read()
        data = self.read()
        print("range:", self.range)
        temperatures = self.parse_data(data)
        return temperatures

    @property
    def min_temp(self) -> int:
        """The minimum temperature range of the device."""
        return -80

    @property
    def max_temp(self) -> int:
        """The maximum temperature range of the device."""
        return 105

    @property
    def min_volt(self) -> int:
        """The minimum voltage output of the device."""
        return 4

    @property
    def max_volt(self) -> int:
        """The maximum voltage output of the device."""
        return 20

    @property
    def range(self) -> float:
        """The temperature range divided by the voltage range.

        This figure is used when convering the raw data to temperatures.
        """
        return (self.max_temp - self.min_temp) / (self.max_volt - self.min_volt)


if __name__ == "__main__":
    serial = Serial("COM4", 57600)
    # serial = Serial()
    device = Seneca(serial)

    data = device.get_temperatures()
