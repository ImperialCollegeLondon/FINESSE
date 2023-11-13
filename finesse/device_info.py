"""Provides common dataclasses about devices for using in backend and frontend."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DeviceParameter:
    """A parameter that a device needs (e.g. baudrate)."""

    name: str
    """Name for the parameter."""

    possible_values: Sequence[Any]
    """Possible values the parameter can take."""

    default_value: Any = None
    """The default value for this parameter.

    A value of None indicates that there is no default value."""

    def __post_init__(self) -> None:
        """Check that default value is valid."""
        if (
            self.default_value is not None
            and self.default_value not in self.possible_values
        ):
            raise RuntimeError(
                f"Default value of {self.default_value} not in possible values"
            )


@dataclass(frozen=True)
class DeviceTypeInfo:
    """Description of a device."""

    description: str
    """A human-readable name for the device."""
    parameters: list[DeviceParameter]
    """The device parameters."""
    class_name: str
    """The name of the device's class including the module name."""


@dataclass(frozen=True)
class DeviceBaseTypeInfo:
    """A generic device type (e.g. stepper motor)."""

    name: str
    """Short name for use in pubsub topics etc."""
    description: str
    """A human-readable name for these types of device."""
    names_short: Sequence[str]
    """A list of possible names for this type of device."""
    names_long: Sequence[str]
    """A list of names for this type of device (human readable)."""


@dataclass(frozen=True)
class DeviceInstanceRef:
    """Information uniquely describing an instance of a particular device type."""

    base_type: str
    """The device base type."""
    name: str | None = None
    """The (optional) name of the device.

    Used for disambiguating devices where there can be multiple instances.
    """

    @staticmethod
    def from_str(s: str) -> DeviceInstanceRef:
        """Convert from a string in the format "base_type.name" or "base_type"."""
        base_type, _, name = s.partition(".")
        return DeviceInstanceRef(base_type, name or None)

    @property
    def topic(self) -> str:
        """Get the partial pubsub topic for this device."""
        topic = self.base_type
        if self.name:
            topic += f".{self.name}"
        return topic
