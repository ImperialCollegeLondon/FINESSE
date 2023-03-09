"""Provides a base class for TC4820 devices or mock devices."""
from decimal import Decimal

from pubsub import pub


class TC4820Base:
    """The base class for TC4820 devices or mock devices."""

    PROPERTIES = {"temperature", "power", "alarm_status", "set_point"}
    """The required properties that all subclasses must have."""

    def __init__(self) -> None:
        """Create a new TC4820Base object.

        Subscribes to incoming requests.
        """
        pub.subscribe(self.request_properties, "tc4820.request")
        pub.subscribe(self.change_set_point, "tc4820.change_set_point")

    def request_properties(self) -> None:
        """Requests that various device properties are sent over pubsub."""
        properties = {}
        for prop in self.PROPERTIES:
            properties[prop] = getattr(self, prop)

        pub.sendMessage("tc4820.response", properties=properties)

    def change_set_point(self, temperature: Decimal) -> None:
        """Change the set point to a new value."""
        self.set_point = temperature
