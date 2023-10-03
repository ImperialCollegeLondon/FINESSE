"""Provides a base class for temperature monitor devices or mock devices."""
from abc import abstractmethod
from decimal import Decimal

from finesse.config import TEMPERATURE_MONITOR_TOPIC
from finesse.hardware.device_base import DeviceBase
from finesse.hardware.plugins import register_base_device_type


@register_base_device_type(TEMPERATURE_MONITOR_TOPIC, "Temperature monitor")
class TemperatureMonitorBase(DeviceBase):
    """The base class for temperature monitor devices or mock devices."""

    @abstractmethod
    def get_temperatures(self) -> list[Decimal]:
        """Get the current temperatures."""
