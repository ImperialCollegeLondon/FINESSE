"""This module provides an interface for querying localhost system time."""
from time import time

from finesse.hardware.plugins.time.time_base import TimeBase


class HostTime(TimeBase, description="Host time"):
    """A time source that queries the system time."""

    def close(self) -> None:
        """Close the connection to the device."""

    def get_time(self) -> float:
        """Get the current time."""
        return time()
