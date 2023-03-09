"""Tests for the DummyTC4820 class."""
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from finesse.hardware.dummy_tc4820 import DummyTC4820


def test_default_alarm_status() -> None:
    """Check the default alarm status."""
    dev = DummyTC4820()
    assert dev.alarm_status == 0


@pytest.mark.parametrize("name", ("temperature", "power", "alarm_status"))
def test_get_properties(name: str) -> None:
    """Test that each of the properties is set up correctly."""
    mock = MagicMock()
    mock.return_value = "MAGIC"
    kwargs = {f"{name}_producer": mock}
    dev = DummyTC4820(**kwargs)
    value = getattr(dev, name)
    assert value == "MAGIC"


@pytest.mark.parametrize("set_point", range(3))
def test_set_point(set_point: int) -> None:
    """Test the set_point attribute behaves as expected."""
    dev = DummyTC4820(initial_set_point=Decimal(10))
    assert dev.set_point == Decimal(10)
    dev.change_set_point(Decimal(set_point))
    assert dev.set_point == Decimal(set_point)
