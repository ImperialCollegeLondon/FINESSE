"""Common functionality for opening and closing USB serial devices."""
import logging
from collections.abc import Callable

from pubsub import pub
from serial import Serial

from ..config import DUMMY_DEVICE_PORT
from .device_base import DeviceBase


def make_device_factory(
    device_factory: Callable[[Serial], DeviceBase],
    dummy_device_factory: Callable[[], DeviceBase],
) -> Callable[[str, int], DeviceBase]:
    """Make a device factory function.

    Args:
        device_factory: A factory function taking a Serial object as an argument
        dummy_device_factory: A factory function taking no arguments and returning a
                              dummy device object
    """

    def create_device(port: str, baudrate: int) -> DeviceBase:
        if port == DUMMY_DEVICE_PORT:
            return dummy_device_factory()
        else:
            serial = Serial(port, baudrate)
            return device_factory(serial)

    return create_device


class SerialManager:
    """A class for managing the opening and closing of USB serial devices.

    When the object receives the "serial.{name}.open" message, a new instance of the
    device will be created, using the serial argument. If the argument is None, a dummy
    device will be called instead. When the "serial.{name}.close" message is received,
    the device will be closed.
    """

    def __init__(
        self,
        name: str,
        device_factory: Callable[[str, int], DeviceBase],
    ) -> None:
        """Create a new SerialManager object.

        Args:
            name: A unique name for the device to be used in pubsub topic names
            device_factory: A factory method taking a port and baudrate as arguments and
                            returning a constructed device
        """
        self.name = name
        self.device: DeviceBase
        self.device_factory = device_factory

        # Listen for open events for this device
        pub.subscribe(self._open, f"serial.{name}.open")

    def _open(self, port: str, baudrate: int) -> None:
        """Open the device.

        Args:
            port: The serial port to use
            baudrate: The baudrate to use
        """
        try:
            # Create a new device object using the provided factory function
            self.device = self.device_factory(port, baudrate)
        except Exception as error:
            logging.error(f"Failed to open device {self.name}: {str(error)}")
            pub.sendMessage(f"serial.{self.name}.error", error=error)
        else:
            # Listen for close events for this device
            pub.subscribe(self._close, f"serial.{self.name}.close")

            # For now, assume all errors are fatal so close the port
            pub.subscribe(self._send_close_message, f"serial.{self.name}.error")

            # Signal that serial device is now open
            pub.sendMessage(f"serial.{self.name}.opened")

            logging.info(f"Opened device {self.name}")

    def _send_close_message(self, error: BaseException) -> None:
        pub.sendMessage(f"serial.{self.name}.close")

    def _close(self) -> None:
        """Close the device.

        It is ensured that devices will only be closed once.
        """
        pub.unsubscribe(self._close, f"serial.{self.name}.close")
        self.device.close()
        del self.device

        logging.info(f"Closed device {self.name}")
