"""Provides a base class for time source devices or mock devices."""
from abc import abstractmethod
from datetime import datetime

from finesse.config import TIME_TOPIC
from finesse.hardware.device import Device


class TimeBase(Device, name=TIME_TOPIC, description="Time source"):
    """The base class for time source devices or mock devices."""

    @abstractmethod
    def get_time(self) -> datetime:
        """Get the current time.

        Returns:
            A datetime instance representing the current time.
        """
