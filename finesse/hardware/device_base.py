"""Provides a base class for all serial devices (and mock devices)."""
from abc import ABC, abstractmethod


class DeviceBase(ABC):
    """A base class for all devices which mandates that they have a close() method."""

    _device_base_type: str
    """A string to be used in pubsub topics etc. which describes the base type."""
    _device_base_description: str
    """A human-readable description for the base type."""
    _device_description: str
    """A human-readable name."""
    _device_names: set[str] | None
    """Possible names for this device (None == any name)."""
    _device_parameters: dict[str, list[str]] = {}
    """Possible parameters that this device type accepts.

    The key represents the parameter name and the value is a list of possible values.
    """

    def __init__(self, name: str | None = None) -> None:
        """Create a new DeviceBase.

        Args:
            name: A name to distinguish devices of the same type.
        """
        self.topic = f"serial.{self._device_base_type}"
        """The name of the root pubsub topic on which this device will broadcast."""

        self.name = name
        """The (optional) name of this device to use in pubsub messages."""

        if not self._device_names:
            if name:
                raise RuntimeError(
                    "Name provided for device which cannot accept names."
                )
            return

        if name not in self._device_names:
            raise RuntimeError("Invalid name given for device")

        self.topic += f".{name}"

    def __del__(self) -> None:
        """Close the device on deletion."""
        self.close()

    @abstractmethod
    def close(self) -> None:
        """Close the connection to the device."""
