"""This module contains interfaces for querying time sources."""

from finesse.hardware.manage_devices import get_device_instance
from finesse.hardware.plugins.time.time_base import TimeBase


def get_time_instance() -> TimeBase | None:
    """Get the instance of the current time source if connected or None."""
    return get_device_instance(TimeBase)
