"""Tests for the DummyTemperatureController class."""
from decimal import Decimal

import pytest

from finesse.hardware.plugins.temperature.dummy_temperature_controller import (
    DummyTemperatureController,
    NoiseParameters,
)


def test_temperature() -> None:
    """Test that the temperature property works."""
    params = NoiseParameters(mean=1.0, standard_deviation=2.0, seed=100)
    dev = DummyTemperatureController("hot_bb", temperature_params=params)
    assert dev._temperature_producer.mean == params.mean
    assert dev._temperature_producer.standard_deviation == params.standard_deviation
    assert dev._temperature_producer.type == Decimal


def test_power() -> None:
    """Test that the power property works."""
    params = NoiseParameters(mean=1.0, standard_deviation=2.0, seed=100)
    dev = DummyTemperatureController("hot_bb", power_params=params)
    assert dev._power_producer.mean == params.mean
    assert dev._power_producer.standard_deviation == params.standard_deviation
    assert dev._power_producer.type == int


@pytest.mark.parametrize("alarm_status", range(2))
def test_alarm_status(alarm_status: int) -> None:
    """Test that the alarm_status property works."""
    dev = DummyTemperatureController("hot_bb", alarm_status=alarm_status)

    # Should report the same status forever
    assert dev.alarm_status == alarm_status
    assert dev.alarm_status == alarm_status


@pytest.mark.parametrize("set_point", range(3))
def test_set_point(set_point: int) -> None:
    """Test the set_point property works."""
    dev = DummyTemperatureController("hot_bb", initial_set_point=Decimal(10))
    assert dev.set_point == Decimal(10)
    dev.change_set_point(Decimal(set_point))
    assert dev.set_point == Decimal(set_point)
