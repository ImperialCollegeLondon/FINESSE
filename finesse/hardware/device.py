"""Provides base classes for all types of devices.

The Device class is the top-level base class from which all devices ultimately inherit.
Concrete classes for devices must not inherit directly from this class, but instead
should inherit from a device base class (defined by passing is_base_type to the class
constructor).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from finesse.device_info import DeviceBaseTypeInfo, DeviceParameter, DeviceTypeInfo

from .plugins import load_all_plugins

_base_types: set[type[Device]] = set()
"""Registry of device base types."""

_device_types: set[type[Device]] = set()
"""Registry of concrete device types."""


def get_device_type_registry() -> dict[DeviceBaseTypeInfo, list[DeviceTypeInfo]]:
    """Return info about device types grouped according to their base type."""
    # Ensure all base types and device types have been registered
    load_all_plugins()

    # Get the base type info and sort it alphabetically by description
    base_types_info = sorted(
        (t.get_device_base_type_info() for t in _base_types),
        key=lambda info: info.description,
    )

    # Preallocate dict with empty lists
    out: dict[DeviceBaseTypeInfo, list[DeviceTypeInfo]] = {
        info: [] for info in base_types_info
    }

    # Get device type info and group by base type
    for device_type in _device_types:
        out[device_type.get_device_base_type_info()].append(
            device_type.get_device_type_info()
        )

    # Sort the device types by name
    for infos in out.values():
        infos.sort(key=lambda info: info.description)

    return out


class AbstractDevice(ABC):
    """An abstract base class for devices."""

    _device_base_type_info: DeviceBaseTypeInfo
    """Information about the device's base type."""
    _device_description: str
    """A human-readable name."""
    _device_parameters: list[DeviceParameter] | None = None
    """Possible parameters that this device type accepts.

    The key represents the parameter name and the value is a list of possible values.
    """

    @abstractmethod
    def close(self) -> None:
        """Close the connection to the device."""

    @classmethod
    def add_device_parameters(cls, *parameters: DeviceParameter) -> None:
        """Add extra parameters for this device class."""
        if cls._device_parameters is None:
            cls._device_parameters = []

        cls._device_parameters.extend(parameters)

    @classmethod
    def get_device_parameters(cls) -> list[DeviceParameter]:
        """Get the parameters for this device class."""
        return cls._device_parameters or []

    @classmethod
    def get_device_base_type_info(cls) -> DeviceBaseTypeInfo:
        """Get information about the base type for this device type."""
        return cls._device_base_type_info

    @classmethod
    def get_device_type_info(cls) -> DeviceTypeInfo:
        """Get information about this device type."""
        return DeviceTypeInfo(
            cls._device_description,
            cls.get_device_parameters(),
            cls.__module__,
            cls.__name__,
        )


class Device(AbstractDevice):
    """A base class for device types.

    This class is the base class for device base types and (indirectly) concrete device
    type classes. Unlike AbstractDevice, it provides an __init_subclass__ method to
    initialise the its subclasses differently depending on whether or not they are
    defined as device base types or not.
    """

    def __init_subclass__(cls, is_base_type: bool = False, **kwargs: Any) -> None:
        """Initialise a device type class.

        Args:
            is_base_type: Whether this class represents a device base type
        """
        # If it is a base class, we initialise it as such
        if is_base_type:
            cls._init_base_type(**kwargs)
            return

        # If it is not, it should inherit from one
        if not set(cls.__bases__).intersection(_base_types):
            raise ValueError(
                f"Class {cls.__name__} must be a device base type or inherit from one."
            )

        # And we initialise it as a concrete device class
        cls._init_device_type(**kwargs)

    @classmethod
    def _init_base_type(
        cls,
        name: str,
        description: str,
        names_short: Sequence[str] = (),
        names_long: Sequence[str] = (),
        **kwargs,
    ) -> None:
        super().__init_subclass__(**kwargs)

        # Store metadata about this base class
        cls._device_base_type_info = DeviceBaseTypeInfo(
            name, description, names_short, names_long
        )

        # Add the class to the registry of base types
        _base_types.add(cls)

    @classmethod
    def _init_device_type(
        cls,
        description: str,
        **kwargs,
    ) -> None:
        super().__init_subclass__(**kwargs)

        # Set device description for this class
        cls._device_description = description

        # Add the class to the registry of device types
        _device_types.add(cls)

    def __init__(self, name: str | None = None) -> None:
        """Create a new DeviceBase.

        Args:
            name: A name to distinguish devices of the same type.
        """
        self.topic = f"device.{self._device_base_type_info.name}"
        """The name of the root pubsub topic on which this device will broadcast."""

        self.name = name
        """The (optional) name of this device to use in pubsub messages."""

        if not self._device_base_type_info.names_short:
            if name:
                raise RuntimeError(
                    "Name provided for device which cannot accept names."
                )
            return

        if name not in self._device_base_type_info.names_short:
            raise RuntimeError("Invalid name given for device")

        self.topic += f".{name}"
