"""Provides a base class for temperature controller devices or mock devices."""
from abc import abstractmethod
from decimal import Decimal
from typing import Any

from pubsub import pub

from ...config import TEMPERATURE_CONTROLLER_TOPIC
from ..device_base import DeviceBase
from ..pubsub_decorators import pubsub_broadcast, pubsub_errors


class TemperatureControllerBase(DeviceBase):
    """The base class for temperature controller devices or mock devices."""

    def __init__(self, name: str) -> None:
        """Create a new TemperatureControllerBase object.

        Subscribes to incoming requests.

        Args:
            name: The name of the device, to distinguish it from others
        """
        super().__init__()
        self.name = name
        topic_base = f"serial.{TEMPERATURE_CONTROLLER_TOPIC}.{self.name}"
        self._request_properties = pubsub_broadcast(
            f"{topic_base}.error", f"{topic_base}.response", "properties"
        )(self.get_properties)
        """Requests that various device properties are sent over pubsub."""

        pub.subscribe(
            self._request_properties,
            f"serial.{TEMPERATURE_CONTROLLER_TOPIC}.{name}.request",
        )

        self._change_set_point = pubsub_errors(f"{topic_base}.error")(
            self.change_set_point
        )
        pub.subscribe(
            self._change_set_point,
            f"serial.{TEMPERATURE_CONTROLLER_TOPIC}.{name}.change_set_point",
        )

    def get_properties(self) -> dict[str, Any]:
        """Get device properties."""
        return {
            prop: getattr(self, prop)
            for prop in ("temperature", "power", "alarm_status", "set_point")
        }

    def change_set_point(self, temperature: Decimal) -> None:
        """Change the set point to a new value."""
        self.set_point = temperature

    @property
    @abstractmethod
    def temperature(self) -> Decimal:
        """The current temperature reported by the device."""

    @property
    @abstractmethod
    def power(self) -> int:
        """The current power output of the device."""

    @property
    @abstractmethod
    def alarm_status(self) -> int:
        """The current error status of the system.

        A value of zero indicates that no error has occurred.
        """

    @property
    @abstractmethod
    def set_point(self) -> Decimal:
        """The set point temperature (in degrees).

        In other words, this indicates the temperature the device is aiming towards.
        """

    @set_point.setter
    @abstractmethod
    def set_point(self, temperature: Decimal) -> None:
        pass  # pragma: no cover
