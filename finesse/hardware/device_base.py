"""Provides a base class for all serial devices (and mock devices)."""
from abc import ABC, abstractmethod

from finesse.device_info import DeviceBaseTypeInfo, DeviceParameter, DeviceTypeInfo


class DeviceBase(ABC):
    """A base class for all devices which mandates that they have a close() method."""

    _device_base_type_info: DeviceBaseTypeInfo
    """Information about the device's base type."""
    _device_description: str
    """A human-readable name."""
    _device_parameters: list[DeviceParameter] = []
    """Possible parameters that this device type accepts.

    The key represents the parameter name and the value is a list of possible values.
    """

    def __init__(self, name: str | None = None) -> None:
        """Create a new DeviceBase.

        Args:
            name: A name to distinguish devices of the same type.
        """
        self.topic = f"serial.{self._device_base_type_info.name}"
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

    def __del__(self) -> None:
        """Close the device on deletion."""
        self.close()

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
