"""This module provides an interface for querying localhost system time."""
from datetime import datetime

from finesse.hardware.plugins.time.time_base import TimeBase


class HostTime(TimeBase, description="Host time"):
    """A time source that queries the system time."""

    def close(self) -> None:
        """Close the connection to the device."""

    def get_time(self) -> datetime:
        """Get the current time.

        Returns:
            A datetime instance representing the current time.
        """
        return datetime.now()
