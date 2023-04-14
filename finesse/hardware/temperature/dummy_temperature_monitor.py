"""This module provides an interface to dummy DP9800 temperature readers."""
import logging
from decimal import Decimal

from pubsub import pub

from ..noise_producer import NoiseProducer
from .temperature_monitor_base import TemperatureMonitorBase


class DummyTemperatureMonitor(TemperatureMonitorBase):
    """A dummy temperature monitor for GUI testing."""

    def __init__(self) -> None:
        """Create a new DummyTemperatureMonitor."""
        super().__init__("dummy")
        self._noise_producer = NoiseProducer(seed=None)

    def close(self) -> None:
        """Close the connection to the device."""
        pub.sendMessage("temperature_monitor.close")
        logging.info("Closed connection to dummy temperature monitor")

    def get_temperatures(self) -> list[Decimal]:
        """Get current temperatures."""
        _BASE_TEMPS = (19, 17, 26, 22, 24, 68, 69, 24)
        noise = self._noise_producer()
        return [Decimal(noise + temp) for temp in _BASE_TEMPS]
