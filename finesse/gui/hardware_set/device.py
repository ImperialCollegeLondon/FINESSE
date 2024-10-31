"""Helper functions for managing connections to devices."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from frozendict import frozendict
from pubsub import pub

from finesse.device_info import DeviceInstanceRef


@dataclass(frozen=True)
class OpenDeviceArgs:
    """Arguments needed to open a device."""

    instance: DeviceInstanceRef
    class_name: str
    params: frozendict[str, Any] = field(default_factory=frozendict)

    def open(self) -> None:
        """Open the device."""
        open_device(self.class_name, self.instance, self.params)

    def close(self) -> None:
        """Close the device."""
        close_device(self.instance)

    @classmethod
    def create(
        cls, instance: str, class_name: str, params: Mapping[str, Any] = frozendict()
    ) -> OpenDeviceArgs:
        """Create an OpenDeviceArgs using basic types."""
        return cls(DeviceInstanceRef.from_str(instance), class_name, frozendict(params))


class ConnectionStatus(Enum):
    """The state of a device that has begun connecting or is already connected.

    Note that there is no DISCONNECTED state, as we do not need to represent
    disconnected devices.
    """

    CONNECTING = 0
    CONNECTED = 1


def open_device(
    class_name: str, instance: DeviceInstanceRef, params: Mapping[str, Any]
) -> None:
    """Open a connection to a device."""
    pub.sendMessage(
        "device.open", class_name=class_name, instance=instance, params=params
    )


def close_device(instance: DeviceInstanceRef) -> None:
    """Close a connection to a device."""
    pub.sendMessage("device.close", instance=instance)
