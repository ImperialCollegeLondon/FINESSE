"""Provides common dataclasses about devices for using in backend and frontend."""
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceParameter:
    """A parameter that a device needs (e.g. baudrate)."""

    name: str
    """Name for the parameter."""

    possible_values: list[str]
    """Possible values the parameter can take."""

    default_value: str | None = None
    """The default value for this parameter."""

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
    module: str
    """The module in which this class resides."""
    class_name: str
    """The name of the device's class."""


@dataclass(frozen=True)
class DeviceBaseTypeInfo:
    """A base device type (e.g. stepper motor)."""

    name: str
    """Short name for use in pubsub topics etc."""
    description: str
    """A human-readable name for these types of device."""
    names_short: Sequence[str]
    """A list of possible names for this type of device."""
    names_long: Sequence[str]
    """A list of names for this type of device (human readable)."""
