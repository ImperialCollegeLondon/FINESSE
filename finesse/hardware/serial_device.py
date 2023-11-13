"""Provides a base class for USB serial devices."""
from __future__ import annotations

from typing import Any

from serial import Serial, SerialException
from serial.tools.list_ports import comports

from finesse.config import BAUDRATES
from finesse.device_info import DeviceParameter
from finesse.hardware.device import AbstractDevice

_serial_ports: dict[str, str] | None = None


def _port_info_to_str(
    vendor_id: int, product_id: int, serial_number: str | None = None, count: int = 0
) -> str:
    """Convert USB port information to a formatted string.

    Args:
        vendor_id: USB vendor ID
        product_id: USB product ID
        serial_number: USB serial number (not always present)
        count: Extra field to distinguish devices
    """
    out = f"{vendor_id:04x}:{product_id:04x}"
    if serial_number:
        out += f" {serial_number}"
    if count > 0:
        out += f" ({count+1})"
    return out


def _get_usb_serial_ports() -> dict[str, str]:
    """Get the ports for connected USB serial devices.

    The list of ports is only requested from the OS once and the result is cached.
    """
    global _serial_ports
    if _serial_ports is not None:
        return _serial_ports

    # Keep track of ports with the same vendor ID, product ID and serial number and
    # assign them an additional number to distinguish them
    counter: dict[tuple[int, int, str | None], int] = {}
    _serial_ports = {}
    for port in comports():
        # Vendor ID is a USB-specific field, so we can use this to check whether the
        # device is USB or not
        if port.vid is None:
            continue

        key = (port.vid, port.pid, port.serial_number)
        if key not in counter:
            counter[key] = 0

        _serial_ports[_port_info_to_str(*key, counter[key])] = port.device
        counter[key] += 1

    # Sort by the string representation of the key
    _serial_ports = dict(sorted(_serial_ports.items(), key=lambda item: item[0]))

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

        # Extra, serial-specific parameters
        cls.add_device_parameters(
            DeviceParameter("port", list(_get_usb_serial_ports().keys())),
            DeviceParameter("baudrate", BAUDRATES, default_baudrate),
        )

    def __init__(self, port: str, baudrate: int) -> None:
        """Create a new serial device."""
        try:
            device = _serial_ports[port]  # type: ignore[index]
        except KeyError:
            raise SerialException(f'Device not present: "{port!s}"')

        self.serial = Serial(port=device, baudrate=baudrate)

    def close(self) -> None:
        """Close the connection to the device."""
        self.serial.close()
