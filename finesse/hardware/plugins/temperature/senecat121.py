"""This module provides an interface to Seneca temperature readers."""
from decimal import Decimal
from typing import Any

import numpy
from serial import SerialException

from finesse.hardware.serial_device import SerialDevice

from .temperature_monitor_base import TemperatureMonitorBase


class SenecaK107Error(Exception):
    """Indicates that an error occurred while communicating with the device."""


class SenecaK107(
    SerialDevice,
    TemperatureMonitorBase,
    description="SenecaK107",
    default_baudrate=57600,
):
    """An interface for the Seneca K107USB serial converter.

    This device communicates through the MODBUS-RTU protocol and outputs data from
    temperature monitor devices. The current connected temperature monitor device is
    the Seneca T121.

    The manual for this device is available at:
    https://www.seneca.it/products/k107usb/doc/installation_manualEN
    """

    def __init__(self, *serial_args: Any, **serial_kwargs: Any) -> None:
        """Create a new SenecaK107.

        Args:
            serial_args: Arguments to Serial constructor
            serial_kwargs: Keyword arguments to Serial constructor
        """
        SerialDevice.__init__(self, *serial_args, **serial_kwargs)
        TemperatureMonitorBase.__init__(self)

    def read(self) -> bytes:
        """Read temperature data from the SenecaK107.

        Returns:
            data: the sequence of bytes read from the device

        Raises:
            SenecaK107Error: Malformed message received from device
        """
        try:
            data = self.serial.read(size=21)
        except SerialException as e:
            raise SenecaK107Error(e)

        # require 21 bytes else checks will fail
        min_length = 21
        if len(data) != min_length:
            raise SenecaK107Error("Insufficient data read from device")

        return data

    def request_read(self) -> None:
        """Write a message to the SenecaK107 to prepare for a read operation.

        A byte array of [1, 3, 0, 2, 0, 8, 229, 204] is written to the device as a
        request to read the data. This byte array was taken from the original C# code.

        Raises:
            SenecaK107Error: Error writing to the device
        """
        try:
            self.serial.write(bytearray([1, 3, 0, 2, 0, 8, 229, 204]))
        except Exception as e:
            raise SenecaK107Error(e)

    def parse_data(self, data: bytes) -> list[Decimal]:
        """Parse temperature data read from the SenecaK107.

        The sequence of bytes is put through the conversion function and translated
        into floats.

        Args:
            data: The bytes read from the device.

        Returns:
            vals: A list of Decimals containing the temperature values recorded
                by the SenecaK107 device.
        """
        dt = numpy.dtype(numpy.uint16).newbyteorder(">")
        ints = numpy.frombuffer(data, dt, 8, 3)
        print("Pre-scaling:", ints)

        # Test for minimum and maximum output values
        # ints = [4000, 20000]

        vals = [Decimal(float(self.calc_temp(val))) for val in ints]
        return vals

    def calc_temp(self, val: numpy.float64) -> numpy.float64:
        """Convert data read from the SenecaK107 device into temperatures.

        Args:
            val: A value from the array described by the data received from the device.

        Returns:
            vals: The converted value.
        """
        temp = (self.range * ((val / 1000) - self.min_volt)) + self.min_temp
        return temp

    def get_temperatures(self) -> list[Decimal]:
        """Get the current temperatures."""
        self.request_read()
        data = self.read()
        temperatures = self.parse_data(data)
        return temperatures

    @property
    def min_temp(self) -> int:
        """The minimum temperature limit of the device."""
        return -80

    @property
    def max_temp(self) -> int:
        """The maximum temperature limit of the device."""
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