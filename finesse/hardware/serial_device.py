"""Provides a base class for USB serial devices."""
from __future__ import annotations

from typing import Any

from serial import Serial
from serial.tools.list_ports import comports

from finesse.config import BAUDRATES
from finesse.device_info import DeviceParameter

from .device import AbstractDevice

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


class SerialDevice(AbstractDevice):
    """A base class for USB serial devices.

    Note that it is not sufficient for a device type class to inherit from this class
    alone: it must also inherit from a device base class. When doing so, this class
    *must* be listed before any other parent classes, otherwise the ABC won't be able to
    find this class's implementation of close() and will complain about missing
    functions.
    """

    serial: Serial
    """Underlying serial device."""

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

    def __init__(self, *serial_args: Any, **serial_kwargs: Any) -> None:
        """Create a new serial device."""
        self.serial = Serial(*serial_args, **serial_kwargs)

    def close(self) -> None:
        """Close the connection to the device."""
        self.serial.close()
