"""Provides a base class for temperature monitor devices or mock devices."""
from abc import abstractmethod

from pubsub import pub

from ...config import TEMPERATURE_MONITOR_TOPIC
from ..device_base import DeviceBase


class TemperatureMonitorBase(DeviceBase):
    """The base class for temperature monitor devices or mock devices.

    Subscribes to incoming requests.
    """

    def __init__(self, name: str) -> None:
        """Create a new TemperatureMonitorBase object."""
        super().__init__()
        pub.subscribe(
            self.send_temperatures, f"serial.{TEMPERATURE_MONITOR_TOPIC}.data.request"
        )

    @abstractmethod
    def send_temperatures(self) -> None:
        """Requests that temperatures are sent over pubsub."""
