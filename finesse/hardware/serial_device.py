"""Provides a base class for USB serial devices."""
from typing import Any

from serial import Serial
from serial.tools.list_ports import comports

from finesse.config import BAUDRATES
from finesse.device_info import DeviceParameter

from .device import Device

_serial_ports: list[str] | None = None


def _get_usb_serial_ports() -> list[str]:
    """Get the ports for connected USB serial devices.

    The list of ports is only requested from the OS once and the result is cached.
    """
    global _serial_ports
    if _serial_ports is not None:
        return _serial_ports

    # Vendor ID is a USB-specific field, so we can use this to check whether the device
    # is USB or not
    _serial_ports = sorted(port.device for port in comports() if port.vid is not None)

    return _serial_ports


class SerialDevice(Device):
    """A base class for USB serial devices.

    Note that it is not sufficient for a device type class to inherit from this class
    alone: it must also inherit from a device base class.
    """

    def __init_subclass__(cls, default_baudrate: int, **kwargs: Any) -> None:
        """Add serial-specific device parameters to the class."""
        super().__init_subclass__(**kwargs)

        # TODO: Allow for adding parameters elsewhere rather than clobbering them
        cls._device_parameters = [
            DeviceParameter("port", _get_usb_serial_ports()),
            DeviceParameter(
                "baudrate", list(map(str, BAUDRATES)), str(default_baudrate)
            ),
        ]

    @classmethod
    def from_params(  # type: ignore[override]
        cls, port: str, baudrate: str, **kwargs: Any
    ) -> Device:
        """Create a new device object from the specified port and baudrate."""
        return cls(Serial(port, int(baudrate)), **kwargs)
