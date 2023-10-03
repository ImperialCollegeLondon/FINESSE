"""Provides a base class for all serial devices (and mock devices)."""
from abc import ABC, abstractmethod


class DeviceBase(ABC):
    """A base class for all devices which mandates that they have a close() method."""

    _device_base_type: str
    """A string to be used in pubsub topics etc. which describes the base type."""
    _device_description: str
    """A human-readable name."""

    def __del__(self) -> None:
        """Close the device on deletion."""
        self.close()

    @abstractmethod
    def close(self) -> None:
        """Close the connection to the device."""
