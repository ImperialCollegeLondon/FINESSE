"""Tests for the DummyTC4820 class."""
from dataclasses import asdict
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import pytest

from finesse.hardware.dummy_tc4820 import DummyTC4820, NoiseParameters


@patch("finesse.hardware.dummy_tc4820.NoiseProducer")
def test_temperature(noise_mock: Mock) -> None:
    """Test that the temperature property works."""
    temperature_mock = MagicMock(return_value=Decimal(10))
    noise_mock.return_value = temperature_mock
    params = NoiseParameters(mean=1.0, standard_deviation=2.0, seed=100)
    dev = DummyTC4820(temperature_params=params)
    noise_mock.assert_any_call(**asdict(params), type=Decimal)
    assert dev.temperature == Decimal(10)


@patch("finesse.hardware.dummy_tc4820.NoiseProducer")
def test_power(noise_mock: Mock) -> None:
    """Test that the power property works."""
    power_mock = MagicMock(return_value=Decimal(10))
    noise_mock.return_value = power_mock
    params = NoiseParameters(mean=1.0, standard_deviation=2.0, seed=100)
    dev = DummyTC4820(power_params=params)
    noise_mock.assert_any_call(**asdict(params), type=int)
    assert dev.power == Decimal(10)


@pytest.mark.parametrize("alarm_status", range(2))
def test_alarm_status(alarm_status: int) -> None:
    """Test that the alarm_status property works."""
    dev = DummyTC4820(alarm_status=alarm_status)

    # Should report the same status forever
    assert dev.alarm_status == alarm_status
    assert dev.alarm_status == alarm_status


@pytest.mark.parametrize("set_point", range(3))
def test_set_point(set_point: int) -> None:
    """Test the set_point property works."""
    dev = DummyTC4820(initial_set_point=Decimal(10))
    assert dev.set_point == Decimal(10)
    dev.change_set_point(Decimal(set_point))
    assert dev.set_point == Decimal(set_point)
