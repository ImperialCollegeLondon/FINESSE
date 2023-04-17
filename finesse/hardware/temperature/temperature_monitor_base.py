"""Provides a base class for temperature monitor devices or mock devices."""
from abc import abstractmethod
from datetime import datetime
from decimal import Decimal

from pubsub import pub

from ...config import TEMPERATURE_MONITOR_TOPIC
from ..device_base import DeviceBase
from ..pubsub_decorators import pubsub_broadcast


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
    def get_temperatures(self) -> list[Decimal]:
        """Get the current temperatures."""

    @pubsub_broadcast(
        f"serial.{TEMPERATURE_MONITOR_TOPIC}.error",
        f"serial.{TEMPERATURE_MONITOR_TOPIC}.data.response",
        "temperatures",
        "time",
    )
    def send_temperatures(self) -> tuple[list[Decimal], float]:
        """Requests that temperatures are sent over pubsub."""
        temperatures = self.get_temperatures()
        time = datetime.now().timestamp()
        return temperatures, time
