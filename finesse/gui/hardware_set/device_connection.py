"""Helper functions for managing connections to devices."""

from collections.abc import Mapping
from typing import Any

from pubsub import pub

from finesse.device_info import DeviceInstanceRef


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
