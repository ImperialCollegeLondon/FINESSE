"""Tests for the TemperatureControllerBase class."""

from decimal import Decimal
from unittest.mock import patch

from finesse.hardware.plugins.temperature.temperature_controller_base import (
    TemperatureControllerBase,
)


class _MockTemperatureController(
    TemperatureControllerBase, description="Mock temperature controller"
):
    def __init__(self) -> None:
        super().__init__("hot_bb")

    @property
    def temperature(self) -> Decimal:
        """The current temperature reported by the device."""
        return Decimal(1)

    @property
    def power(self) -> float:
        """The current power output of the device."""
        return 2.0

    @property
    def alarm_status(self) -> int:
        """The current error status of the system.

        A value of zero indicates that no error has occurred.
        """
        return 3

    @property
    def set_point(self) -> Decimal:
        """The set point temperature (in degrees).

        In other words, this indicates the temperature the device is aiming towards.
        """
        return Decimal(4)

    @set_point.setter
    def set_point(self, temperature: Decimal) -> None:
        pass  # pragma: no cover


def test_init() -> None:
    """Test TemperatureControllerBase's constructor."""
    with patch.object(_MockTemperatureController, "subscribe") as subscribe_mock:
        dev = _MockTemperatureController()

        assert subscribe_mock.call_count == 2
        subscribe_mock.assert_any_call(dev.change_set_point, "change_set_point")
        subscribe_mock.assert_any_call(
            dev.get_properties, "request", "response", "properties"
        )
