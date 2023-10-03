"""Plugins for the hardware module."""
import importlib
import pkgutil
import sys
from types import ModuleType

from finesse.hardware.device_base import DeviceBase

_base_types: set[type[DeviceBase]] = set()
_device_types: set[type[DeviceBase]] = set()


def register_device_type(description: str):
    """Register a new device type.

    Args:
        description: A human-readable name for this device.
    """

    def wrapped(cls: type[DeviceBase]):
        cls._device_description = description
        _device_types.add(cls)
        return cls

    return wrapped


def register_base_device_type(name: str, description: str):
    """A decorator for registering a new device base type.

    Args:
        name: Short name to be used in pubsub topics etc.
        description: Human-readable name
    """

    def wrapped(cls: type[DeviceBase]):
        global _base_types
        cls._device_base_type = name
        cls._device_description = description
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


def load_device_types() -> dict[str, list[type[DeviceBase]]]:
    """Load all the device types from this module and its submodules.

    Returns:
        A dict containing the device types, grouped by the names of base types
    """
    _import_recursively(sys.modules[__name__])

    out: dict[str, list[type[DeviceBase]]] = {
        t._device_base_type: [] for t in _base_types
    }
    for t in _device_types:
        key = t._device_base_type

        try:
            out[key].append(t)
        except KeyError:
            raise RuntimeError(
                f"{t.__name__} does not have a recognised device base type"
            )

    # Sort values
    for val in out.values():
        val.sort(key=lambda v: v._device_description)

    # Sort keys
    return dict(sorted(out.items()))
