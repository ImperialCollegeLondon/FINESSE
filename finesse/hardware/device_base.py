"""Provides a base class for all serial devices (and mock devices)."""
from abc import ABC, abstractmethod


class DeviceBase(ABC):
    """A base class for all devices which mandates that they have a close() method."""

    def __del__(self) -> None:
        """Close the device on deletion."""
        self.close()

    @abstractmethod
    def close(self) -> None:
        """Close the connection to the device."""
