"""Provides a common device type dataclass for using in backend and frontend."""
from dataclasses import dataclass


@dataclass
class DeviceType:
    """Description of a device."""

    description: str
    """A human-readable name for the device."""
    params: dict[str, list[str]]
    """The device parameters and possible values."""
