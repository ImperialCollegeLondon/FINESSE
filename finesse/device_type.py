"""Provides a common device type dataclass for using in backend and frontend."""
from collections.abc import Iterable
from dataclasses import dataclass


class DeviceParameter:
    """A parameter that a device needs (e.g. baudrate)."""

    def __init__(
        self,
        name: str,
        possible_values: Iterable[str],
        default_value: str | None = None,
    ) -> None:
        """Create a new device parameter."""
        self.name = name
        """Name for the parameter."""

        self.possible_values = list(possible_values)
        """Possible values the parameter can take."""

        if default_value is not None and default_value not in self.possible_values:
            raise RuntimeError(
                f"Default value of {default_value} not in possible values"
            )

        self.default_value = default_value
        """The default value for this parameter."""


@dataclass
class DeviceType:
    """Description of a device."""

    description: str
    """A human-readable name for the device."""
    parameters: list[DeviceParameter]
    """The device parameters."""
