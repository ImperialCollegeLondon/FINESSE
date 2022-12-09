"""This module provides an interface to TC4820 temperature controllers.

TODO: I've used float throughout this module, but a decimal type may be more appropriate
and prevent rounding errors.
"""
import logging
from typing import Any

from serial import Serial


class TC4820:
    """An interface for TC4820 temperature controllers."""

    MAX_POWER = 511
    """The maximum value for the power property."""

    def __init__(
        self, port: str, baudrate: int = 115200, *serial_args: Any, **serial_kwargs: Any
    ) -> None:
        """Create a new TC4820.

        Args:
            port: Serial port name
            baudrate: Serial port baudrate
            serial_args: Extra arguments to Serial constructor
            serial_kwargs: Extra keyword arguments to Serial constructor
        """
        self.serial = Serial(port, baudrate, *serial_args, **serial_kwargs)

    def read_int(self) -> int:
        """Read a message from the TC4820 and decode the number as a signed integer."""
        # TODO: Handle errors?
        message = self.serial.read_until(b"^").decode("ascii")

        if len(message) != 8 or message[0] != "*" or message[-1] != "^":
            raise ValueError("Malformed message received: {message}")

        if message == "*XXXX60^":
            raise ValueError("Bad checksum sent")

        if message[6:7] != TC4820.checksum(message[1:5]):
            raise ValueError("Bad checksum received")

        # Turn the hex string into raw bytes, then convert the raw bytes to a signed int
        raw_bytes = bytes.fromhex(message[1:5])
        return int.from_bytes(raw_bytes, byteorder="big", signed=True)

    def read_float(self) -> float:
        """Read a message from the TC4820 and decode the number as a float.

        Float values are encoded as 10x their value then converted to an int.
        """
        return self.read_int() / 10.0

    def write(self, command: str) -> None:
        """Write a message to the TC4820.

        Args:
            command: The string command to send
        """
        checksum = TC4820.checksum(command)
        message = f"*{command}{checksum}\r"
        self.serial.write(message.encode("ascii"))

    @property
    def temperature(self) -> float:
        """The current temperature reported by the device."""
        self.write("010000")
        return self.read_float()

    @property
    def power(self) -> int:
        """The current power output of the device."""
        self.write("020000")
        return self.read_int()

    @property
    def alarm_status(self) -> int:
        """The current error status of the system.

        A value of zero indicates that no error has occurred.

        TODO: Figure out what the error codes mean
        """
        self.write("030000")
        return self.read_int()

    @property
    def set_point(self) -> float:
        """The set point temperature (in degrees).

        In other words, this indicates the temperature the device is aiming towards.
        """
        self.write("500000")
        return self.read_float()

    @set_point.setter
    def set_point(self, temperature: float) -> None:
        # Convert to an int for transmission
        val = round(temperature * 10.0)

        # Values outside this range can't be properly encoded
        if val < 0 or val > 0xFFFF:
            raise ValueError("Temperature provided is out of range")

        # Send the message
        self.write(f"1c{val:0{4}x}")

        # The device now returns the new set point value. Check that it's what we asked
        # for.
        if self.read_int() != val:
            logging.warn(
                "The set point returned by the device differs from the one requested"
            )

    @staticmethod
    def checksum(message: str) -> str:
        """Calculate a checksum for a message sent or received."""
        csum = sum(message.encode("ascii")) & 0xFF
        return f"{csum:0{2}x}"


if __name__ == "__main__":
    import sys

    dev = TC4820(sys.argv[1])

    # Allow user to test setting the set point
    if len(sys.argv) > 2:
        temperature = float(sys.argv[2])
        dev.set_point = temperature
        print(f"New set point: {temperature}")

    # Print out device properties
    for key in ("temperature", "power", "alarm_status", "set_point"):
        print(f"{key}: {getattr(dev, key)}")
