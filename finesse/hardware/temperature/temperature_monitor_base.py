"""Provides a base class for temperature monitor devices or mock devices."""
import logging
from abc import abstractmethod
from datetime import datetime
from decimal import Decimal

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
                "temperature_monitor.data.response",
                temperatures=temperatures,
                time=datetime.now().timestamp(),
            )

    def _error_occurred(self, exception: BaseException) -> None:
        """Log and communicate that an error occurred."""
        logging.error(f"Error during temperature monitor query:\t{exception}")
        pub.sendMessage("temperature_monitor.error", message=str(exception))
