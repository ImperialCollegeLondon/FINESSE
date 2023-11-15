"""Provides a base class for temperature monitor devices or mock devices."""
from abc import abstractmethod
from decimal import Decimal

import numpy

from finesse.config import TEMPERATURE_MONITOR_TOPIC
from finesse.hardware.device import Device

TemperatureSequence = list[Decimal | numpy.float64]


class TemperatureMonitorBase(
    Device,
    is_base_type=True,
    name=TEMPERATURE_MONITOR_TOPIC,
    description="Temperature monitor",
):
    """The base class for temperature monitor devices or mock devices."""

    @abstractmethod
    def get_temperatures(self) -> TemperatureSequence:
        """Get the current temperatures."""
