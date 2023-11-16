"""Provides a base class for temperature monitor devices or mock devices."""
from abc import abstractmethod
from collections.abc import Sequence

from finesse.config import TEMPERATURE_MONITOR_TOPIC
from finesse.hardware.device import Device


class TemperatureMonitorBase(
    Device,
    is_base_type=True,
    name=TEMPERATURE_MONITOR_TOPIC,
    description="Temperature monitor",
):
    """The base class for temperature monitor devices or mock devices."""

    @abstractmethod
    def get_temperatures(self) -> Sequence:
        """Get the current temperatures."""
