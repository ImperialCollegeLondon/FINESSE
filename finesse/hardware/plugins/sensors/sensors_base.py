"""Provides a base class for communicating sensor readings."""

from abc import abstractmethod
from collections.abc import Sequence
from math import isnan

from PySide6.QtCore import QTimer

from finesse.config import SENSORS_TOPIC
from finesse.hardware.device import Device
from finesse.sensor_reading import SensorReading


class SensorsBase(
    Device,
    name=SENSORS_TOPIC,
    description="Sensor devices",
    parameters={"poll_interval": "How often to poll the sensor device (seconds)"},
):
    """Base device class for sensors devices.

    These devices can be polled with the request_readings() method and should respond by
    calling send_readings_message() with new sensor values (at some point).
    """

    def __init__(self, poll_interval: float = float("nan")) -> None:
        """Create a new SensorsBase.

        Args:
            poll_interval: How often to poll the sensor device (seconds). If set to nan,
                           the device will only be polled once on device open
        """
        super().__init__()

        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self.request_readings)
        if not isnan(poll_interval):
            self._poll_timer.start(int(poll_interval * 1000))

        # Poll device once on open.
        # TODO: Run this synchronously so we can check that things work before the
        # device.opened message is sent
        self.request_readings()

    @abstractmethod
    def request_readings(self) -> None:
        """Request new sensor readings from the device."""

    def send_readings_message(self, readings: Sequence[SensorReading]) -> None:
        """Send a pubsub message containing new readings from the sensors."""
        self.send_message("data", readings=readings)

    def close(self) -> None:
        """Close the device."""
        self._poll_timer.stop()
        super().close()
