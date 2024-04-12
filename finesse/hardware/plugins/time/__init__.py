"""This module contains interfaces for querying time sources."""
from datetime import datetime

from finesse.hardware.manage_devices import get_device_instance
from finesse.hardware.plugins.time.time_base import TimeBase


def get_time_instance() -> TimeBase | None:
    """Get the instance of the current time source if connected or None."""
    return get_device_instance(TimeBase)


def get_time() -> datetime:
    """Read the current time, with optional time offset.

    If the time device is not connected or the operation fails, local time is returned.
    """
    timestamp = datetime.now().timestamp()

    if dev := get_time_instance():
        try:
            timestamp += dev.get_time_offset()
        except Exception as error:
            dev.send_error_message(error)

    return datetime.fromtimestamp(timestamp)
