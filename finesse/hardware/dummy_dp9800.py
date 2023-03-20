"""This module provides an interface to dummy DP9800 temperature readers."""
import logging

from pubsub import pub
from serial import EIGHTBITS, PARITY_NONE, STOPBITS_ONE

from .dp9800 import DP9800


class DummyDP9800(DP9800):
    """A fake DP9800 device used for unit tests etc."""

    def __init__(self) -> None:
        """Open the connection to the device."""
        self.in_waiting: int = 0
        self._sysflag: str = ""

        pub.sendMessage("dp9800.open")
        pub.subscribe(self.send_temperatures, "dp9800.data.request")

    @staticmethod
    def create(
        port: str = "",
        baudrate: int = 38400,
        bytesize: int = EIGHTBITS,
        parity: str = PARITY_NONE,
        stopbits: int = STOPBITS_ONE,
        timeout: float = 2.0,
        max_attempts: int = 3,
    ) -> "DummyDP9800":
        """Create the device."""
        return DummyDP9800()

    def close(self) -> None:
        """Close the connection to the device."""
        pub.sendMessage("dp9800.close")
        logging.info("Closed connection to DP9800")

    def read(self) -> bytes:
        """Mimic reading data from the device.

        Returns:
            data: sequence of bytes representative of that read
                  from the physical device
        """
        num_bytes_to_read = self.in_waiting
        if num_bytes_to_read == 0:
            data = b""
        else:
            data = (
                b"\x02T   27.16   19.13   17.61   26.49  850.00"
                + b"   24.35   68.65   69.92   24.1986\x03M\x00"
            )

        logging.info(f"Read {len(data)} bytes from DP9800")
        self.in_waiting = 0
        return data

    def write(self, command: bytes) -> int:
        """Pretend to write data to the device.

        Returns:
            the number of bytes that would be written to the device
        """
        logging.info(f"Wrote {len(command)} bytes to DP9800")
        self.in_waiting = 79
        return len(command)
