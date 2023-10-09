"""Plugins for the hardware module."""
import importlib
import pkgutil
import sys
from collections.abc import Sequence
from functools import partial
from types import ModuleType

from serial import Serial
from serial.tools.list_ports import comports

from finesse.config import BAUDRATES
from finesse.device_info import DeviceBaseTypeInfo, DeviceParameter
from finesse.hardware.device_base import DeviceBase

_base_types: set[type[DeviceBase]] = set()
_device_types: set[type[DeviceBase]] = set()
_serial_ports: list[str] | None = None


def _get_usb_serial_ports() -> list[str]:
    """Get the ports for connected USB serial devices.

    The list of ports is only requested from the OS once and the result is cached.
    """
    global _serial_ports
    if _serial_ports:
        return _serial_ports

    # Vendor ID is a USB-specific field, so we can use this to check whether the device
    # is USB or not
    _serial_ports = sorted(port.device for port in comports() if port.vid is not None)

    return _serial_ports


def register_device_type(description: str):
    """Register a new device type.

    Args:
        description: A human-readable name for this device.
    """

    def wrapped(cls: type[DeviceBase]):
        cls._device_description = description
        if cls in _device_types:
            raise RuntimeError(f"{cls.__name__} is already registered as device type")

        _device_types.add(cls)
        return cls

    return wrapped


def _serial_from_params(cls: type[DeviceBase], port: str, baudrate: str) -> DeviceBase:
    """Create a new device object from the specified port and baudrate."""
    return cls(Serial(port, int(baudrate)))


def register_serial_device_type(description: str, default_baudrate: int):
    """Register a new serial device type.

    Args:
        description: A human-readable name for this device.
        default_baudrate: The default baudrate for this device.
    """

    def wrapped(cls: type[DeviceBase]):
        cls._device_parameters = [
            DeviceParameter("port", _get_usb_serial_ports()),
            DeviceParameter(
                "baudrate", list(map(str, BAUDRATES)), str(default_baudrate)
            ),
        ]

        # Override the default implementation to provide a factory function which
        # accepts port and baudrate directly rather than a Serial object
        cls.from_params = partial(_serial_from_params, cls)  # type: ignore

        # Also apply the register_device_type() decorator
        return register_device_type(description)(cls)

    return wrapped


def register_device_base_type(
    name: str,
    description: str,
    names_short: Sequence[str] = (),
    names_long: Sequence[str] = (),
):
    """A decorator for registering a new device base type.

    Args:
        name: Short name to be used in pubsub topics etc.
        description: Human-readable name
        names_short: Possible names for devices (short)
        names_long: Possible names for devices (human readable)
    """
    if len(names_short) != len(names_long):
        raise RuntimeError("Both short and long names must be provided.")

    def wrapped(cls: type[DeviceBase]):
        cls._device_base_type_info = DeviceBaseTypeInfo(
            name, description, names_short, names_long
        )
        _base_types.add(cls)
        return cls

    return wrapped


def _import_recursively(module: ModuleType) -> None:
    """Recursively import module's submodules."""
    if hasattr(module, "__path__"):
        for modinfo in pkgutil.iter_modules(module.__path__):
            _import_recursively(
                importlib.import_module(f"{module.__name__}.{modinfo.name}")
            )


def load_device_types() -> tuple[set[type[DeviceBase]], set[type[DeviceBase]]]:
    """Load all the device types from this module and its submodules.

    Returns:
        The base types and device types
    """
    _import_recursively(sys.modules[__name__])
    return _base_types, _device_types
