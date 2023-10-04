"""Plugins for the hardware module."""
import importlib
import pkgutil
import sys
from types import ModuleType

from serial.tools.list_ports import comports

from finesse.config import BAUDRATES
from finesse.device_type import DeviceParameter
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


def register_serial_device_type(description: str, default_baudrate: int):
    """Register a new serial device type.

    Args:
        description: A human-readable name for this device.
        default_baudrate: The default baudrate for this device.
    """

    def wrapped(cls: type[DeviceBase]):
        cls._device_parameters = [
            DeviceParameter("port", _get_usb_serial_ports()),
            DeviceParameter("baudrate", map(str, BAUDRATES), str(default_baudrate)),
        ]
        return register_device_type(description)(cls)

    return wrapped


def register_base_device_type(
    name: str, description: str, names: set[str] | None = None
):
    """A decorator for registering a new device base type.

    Args:
        name: Short name to be used in pubsub topics etc.
        description: Human-readable name
        names: Possible names for devices
    """

    def wrapped(cls: type[DeviceBase]):
        global _base_types
        cls._device_base_type = name
        cls._device_base_description = description
        cls._device_names = names
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


def load_device_types() -> dict[str, tuple[set[str] | None, list[type[DeviceBase]]]]:
    """Load all the device types from this module and its submodules.

    Returns:
        A dict containing the device types, grouped by the names of base types
    """
    _import_recursively(sys.modules[__name__])

    out: dict[str, tuple[set[str] | None, list[type[DeviceBase]]]] = {
        t._device_base_type: (t._device_names, []) for t in _base_types
    }
    for t in _device_types:
        key = t._device_base_type

        try:
            out[key][1].append(t)
        except KeyError:
            raise RuntimeError(
                f"{t.__name__} does not have a recognised device base type"
            )

    # Sort values
    for val in out.values():
        val[1].sort(key=lambda v: v._device_description)

    # Sort keys
    return dict(sorted(out.items()))
