"""Provides a base class for temperature monitor devices or mock devices."""
import logging
from abc import abstractmethod
from datetime import datetime
from decimal import Decimal

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
    def get_temperatures(self) -> list[Decimal]:
        """Get the current temperatures."""

    def send_temperatures(self) -> None:
        """Requests that temperatures are sent over pubsub."""
        try:
            temperatures = self.get_temperatures()
        except Exception as e:
            self._error_occurred(e)
        else:
            pub.sendMessage(
                f"serial.{TEMPERATURE_MONITOR_TOPIC}.data.response",
                temperatures=temperatures,
                time=datetime.now().timestamp(),
            )

    def _error_occurred(self, exception: BaseException) -> None:
        """Log and communicate that an error occurred."""
        logging.error(f"Error during temperature monitor query:\t{exception}")
        pub.sendMessage(
            f"serial.{TEMPERATURE_MONITOR_TOPIC}.error", message=str(exception)
        )
