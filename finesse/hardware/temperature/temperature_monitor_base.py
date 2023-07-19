"""Provides a base class for temperature monitor devices or mock devices."""
from abc import abstractmethod
from decimal import Decimal

from ..device_base import DeviceBase


class TemperatureMonitorBase(DeviceBase):
    """The base class for temperature monitor devices or mock devices."""

    @abstractmethod
    def get_temperatures(self) -> list[Decimal]:
        """Get the current temperatures."""
