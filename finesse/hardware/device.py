"""Provides base classes for all types of devices.

The Device class is the top-level base class from which all devices ultimately inherit.
The DeviceBaseType is a base class for *types* of devices (e.g. a stepper motor). All
concrete classes for devices must inherit from a particular DeviceBaseType.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from finesse.device_info import DeviceBaseTypeInfo, DeviceParameter, DeviceTypeInfo

from .plugins import load_all_plugins

_base_types: set[type[DeviceBaseType]] = set()
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


class Device(ABC):
    """A base class for all devices."""

    _device_base_type_info: DeviceBaseTypeInfo
    """Information about the device's base type."""
    _device_description: str
    """A human-readable name."""
    _device_parameters: list[DeviceParameter] = []
    """Possible parameters that this device type accepts.

    The key represents the parameter name and the value is a list of possible values.
    """

    def __init_subclass__(cls, description: str | None = None, **kwargs: Any) -> None:
        """Initialise a device type class.

        While the description argument has to be optional to allow for non-concrete
        classes to inherit from Device, it is mandatory to include it, else the device
        type class will not be added to the registry.

        Args:
            description: Human-readable name for this device type.
        """
        # Forward keyword args to allow for multiple inheritance
        super().__init_subclass__(**kwargs)

        # **HACK**: Allow callers to omit this arg in the case that they are
        # non-concrete
        if not description:
            return

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

    @abstractmethod
    def close(self) -> None:
        """Close the connection to the device."""

    @classmethod
    def get_device_base_type_info(cls) -> DeviceBaseTypeInfo:
        """Get information about the base type for this device type."""
        return cls._device_base_type_info

    @classmethod
    def get_device_type_info(cls) -> DeviceTypeInfo:
        """Get information about this device type."""
        return DeviceTypeInfo(
            cls._device_description,
            cls._device_parameters,
            cls.__module__,
            cls.__name__,
        )

    @classmethod
    def from_params(cls, **kwargs: Any) -> Device:
        """Create an instance of this object from the specified keyword args."""
        return cls(**kwargs)


class DeviceBaseType(Device):
    """A class representing a type of device (e.g. a stepper motor)."""

    def __init_subclass__(
        cls,
        **kwargs,
    ) -> None:
        """Initialise a class representing a device base type.

        NB: Only classes which inherit from DeviceBaseClass *directly* are counted as
        base types.
        """
        if DeviceBaseType in cls.__bases__:
            cls._init_base_type(**kwargs)
        else:
            # For all other cases, just call the parent's __init_subclass__
            super().__init_subclass__(**kwargs)

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
