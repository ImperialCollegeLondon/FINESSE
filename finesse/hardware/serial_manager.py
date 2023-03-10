"""Common functionality for opening and closing USB serial devices."""
from collections.abc import Callable

from pubsub import pub
from serial import Serial

from ..config import DUMMY_DEVICE_PORT
from .device_base import DeviceBase


class SerialManager:
    """A class for managing the opening and closing of USB serial devices.

    When the object receives the "serial.{name}.open" message, a new instance of the
    device will be created, using the serial argument. If the argument is None, a dummy
    device will be called instead. When the "serial.{name}.open" message is received,
    the device will be closed.
    """

    def __init__(
        self,
        name: str,
        device_ctor: Callable[[Serial], DeviceBase],
        dummy_device_ctor: Callable[[], DeviceBase],
    ) -> None:
        """Create a new SerialManager object.

        Args:
            name: A unique name for the device to be used in pubsub topic names
            device_ctor: A constructor for the real device (accepting a Serial object)
            dummy_device_ctor: A constructor for the dummy device
        """
        self.name = name
        self.device: DeviceBase
        self.device_ctor = device_ctor
        self.dummy_device_ctor = dummy_device_ctor

        # Listen for open events for this device
        pub.subscribe(self._open, f"serial.{name}.open")

    def _open(self, port: str, baudrate: int) -> None:
        """Open the device.

        If the port is "Dummy", then a dummy device will be created.

        Args:
            port: The serial port to use
            baudrate: The baudrate to use
        """
        try:
            if port == DUMMY_DEVICE_PORT:
                self.device = self.dummy_device_ctor()
            else:
                serial = Serial(port, baudrate)
                self.device = self.device_ctor(serial)
        except Exception as error:
            pub.sendMessage(f"serial.{self.name}.error", error=error)
        else:
            # Listen for close events for this device
            pub.subscribe(self._close, f"serial.{self.name}.close")

            # For now, assume all errors are fatal so close the port
            pub.subscribe(self._send_close_message, f"serial.{self.name}.error")

            # Signal that serial device is now open
            pub.sendMessage(f"serial.{self.name}.opened")

    def _send_close_message(self, error: BaseException) -> None:
        pub.sendMessage(f"serial.{self.name}.close")

    def _close(self) -> None:
        """Close the device.

        It is ensured that devices will only be closed once.
        """
        pub.unsubscribe(self._close, f"serial.{self.name}.close")
        self.device.close()
        del self.device
