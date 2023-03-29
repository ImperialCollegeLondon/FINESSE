"""This module provides an interface to dummy DP9800 temperature readers."""
import logging
from datetime import datetime
from decimal import Decimal

from pubsub import pub

from ..noise_producer import NoiseProducer
from .temperature_monitor_base import TemperatureMonitorBase


class DummyTemperatureMonitor(TemperatureMonitorBase):
    """A dummy temperature monitor for GUI testing."""

    def __init__(self) -> None:
        """Create a new DummyTemperatureMonitor."""
        super().__init__("dummy")

    def close(self) -> None:
        """Close the connection to the device."""
        pub.sendMessage("temperature_monitor.close")
        logging.info("Closed connection to dummy temperature monitor")

    def send_temperatures(self) -> None:
        """Publish fluctuating temperatures."""
        noise = NoiseProducer(seed=datetime.now().second)()

        time_now = datetime.now().timestamp()
        temperatures = [
            Decimal(19 + noise),
            Decimal(17 + noise),
            Decimal(26 + noise),
            Decimal(850.00),
            Decimal(24 + noise),
            Decimal(68 + noise),
            Decimal(69 + noise),
            Decimal(24 + noise),
        ]
        pub.sendMessage(
            "temperature_monitor.data.response",
            temperatures=temperatures,
            time=time_now,
        )
