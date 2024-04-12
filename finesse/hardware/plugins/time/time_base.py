"""Provides a base class for time source devices or mock devices."""

from abc import abstractmethod

from finesse.config import TIME_TOPIC
from finesse.hardware.device import Device


class TimeBase(Device, name=TIME_TOPIC, description="Time source"):
    """The base class for time source devices or mock devices."""

    @abstractmethod
    def get_time_offset(self) -> float:
        """Get the current time offset.

        Returns:
            A float representing the current time offset.
        """
