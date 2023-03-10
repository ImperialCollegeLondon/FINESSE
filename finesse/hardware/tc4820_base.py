"""Provides a base class for TC4820 devices or mock devices."""
from abc import ABC, abstractmethod
from decimal import Decimal

from pubsub import pub


class TC4820Base(ABC):
    """The base class for TC4820 devices or mock devices."""

    def __init__(self, name: str) -> None:
        """Create a new TC4820Base object.

        Subscribes to incoming requests.

        Args:
            name: The name of the device, to distinguish it from others
        """
        super().__init__()
        self.name = name
        pub.subscribe(self.request_properties, f"tc4820.{name}.request")
        pub.subscribe(self.change_set_point, f"tc4820.{name}.change_set_point")

    def request_properties(self) -> None:
        """Requests that various device properties are sent over pubsub."""
        properties = {}
        for prop in ("temperature", "power", "alarm_status", "set_point"):
            properties[prop] = getattr(self, prop)

        pub.sendMessage(f"tc4820.{self.name}.response", properties=properties)

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
