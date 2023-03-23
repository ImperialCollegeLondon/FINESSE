"""This module provides an interface to dummy DP9800 temperature readers."""
import logging

from pubsub import pub

from .dp9800 import DP9800, DP9800Error


class DummyDP9800(DP9800):
    """A fake DP9800 device used for unit tests etc."""

    def __init__(self) -> None:
        """Open the connection to the device."""
        self.in_waiting: int = 0
        self._sysflag: str = ""

        logging.info("Opened connection to dummy DP9800")
        pub.subscribe(self.send_temperatures, "temperature_monitor.data.request")
        pub.sendMessage("temperature_monitor.open")

    def close(self) -> None:
        """Close the connection to the device."""
        pub.sendMessage("temperature_monitor.close")
        logging.info("Closed connection to DP9800")

    def read(self) -> bytes:
        """Mimic reading data from the device.

        Returns:
            data: sequence of bytes representative of that read
                  from the physical device
        """
        if self.in_waiting == 0:
            raise DP9800Error("No data waiting to be read")

        data = (
            b"\x02T   27.16   19.13   17.61   26.49  850.00"
            + b"   24.35   68.65   69.92   24.1986\x03M\x00"
        )

        self.in_waiting = 0
        return data

    def request_read(self) -> None:
        """Mimic writing to the device to prepare for a read operation.

        Returns:
            the number of bytes that would be written to the device
        """
        self.in_waiting = 79
