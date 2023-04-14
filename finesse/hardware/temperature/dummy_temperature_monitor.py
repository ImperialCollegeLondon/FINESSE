"""This module provides an interface to dummy DP9800 temperature readers."""
from datetime import datetime
from decimal import Decimal

from pubsub import pub

from ...config import TEMPERATURE_MONITOR_TOPIC
from ..noise_producer import NoiseProducer
from .temperature_monitor_base import TemperatureMonitorBase


class DummyTemperatureMonitor(TemperatureMonitorBase):
    """A dummy temperature monitor for GUI testing."""

    def __init__(self) -> None:
        """Create a new DummyTemperatureMonitor."""
        super().__init__("dummy")
        self._noise_producer = NoiseProducer(seed=datetime.now().second)

    def close(self) -> None:
        """Close the connection to the device."""

    def send_temperatures(self) -> None:
        """Publish fluctuating temperatures."""
        _BASE_TEMPS = (19, 17, 26, 22, 24, 68, 69, 24)
        noise = self._noise_producer()
        temperatures = [Decimal(noise + temp) for temp in _BASE_TEMPS]
        time_now = datetime.now().timestamp()

        pub.sendMessage(
            f"serial.{TEMPERATURE_MONITOR_TOPIC}.data.response",
            temperatures=temperatures,
            time=time_now,
        )
