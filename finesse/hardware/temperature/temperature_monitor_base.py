"""Provides a base class for temperature monitor devices or mock devices."""
import logging
from abc import abstractmethod

from pubsub import pub

from ..device_base import DeviceBase


class TemperatureMonitorBase(DeviceBase):
    """The base class for temperature monitor devices or mock devices."""

    def __init__(self, name: str) -> None:
        """Create a new TemperatureMonitorBase object."""
        super().__init__()

        logging.info(f"Opened connection to {name} temperature monitor")
        pub.sendMessage("temperature_monitor.open")
        pub.subscribe(self.send_temperatures, "temperature_monitor.data.request")

    @abstractmethod
    def send_temperatures(self) -> None:
        """Requests that temperatures are sent over pubsub."""
