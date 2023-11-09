"""Tests for the EventCounter class."""
from collections.abc import Sequence
from contextlib import nullcontext as does_not_raise
from typing import Any
from unittest.mock import MagicMock

import pytest

from finesse.event_counter import EventCounter


def test_init() -> None:
    """Test EventCounter's constructor."""
    on_target_reached = MagicMock()
    on_below_target = MagicMock()
    counter = EventCounter(on_target_reached, on_below_target, target_count=1)
    assert counter._count == 0
    assert counter._target_count == 1
    assert counter._on_target_reached is on_target_reached
    assert counter._on_below_target is on_below_target


def test_init_with_devices(subscribe_mock: MagicMock) -> None:
    """Test EventCounter's constructor when device names are given as arguments."""
    counter = EventCounter(MagicMock(), MagicMock(), device_names=("my_device",))
    assert counter._target_count == 1
    subscribe_mock.assert_any_call(counter.increment, "device.opened.my_device")
    subscribe_mock.assert_any_call(counter.decrement, "device.closed.my_device")


@pytest.mark.parametrize(
    "target_count,device_names,raises",
    (
        (
            target_count,
            device_names,
            pytest.raises(ValueError)
            if target_count is None and not device_names
            else does_not_raise(),
        )
        for target_count in (None, 2)
        for device_names in ((), ("device",))
    ),
)
def test_init_missing_args(
    target_count: int | None, device_names: Sequence[str], raises: Any
) -> None:
    """Test that an error is raised when required arguments are missing."""
    with raises:
        EventCounter(MagicMock(), MagicMock(), target_count, device_names)


def test_increment_call() -> None:
    """Test the increment() method when callback is called."""
    on_target_reached = MagicMock()
    on_below_target = MagicMock()
    counter = EventCounter(on_target_reached, on_below_target, target_count=1)
    counter.increment()
    on_target_reached.assert_called_once_with()
    on_below_target.assert_not_called()


def test_increment_no_call() -> None:
    """Test the increment() method when callback is not called."""
    on_target_reached = MagicMock()
    on_below_target = MagicMock()
    counter = EventCounter(on_target_reached, on_below_target, target_count=2)
    counter.increment()
    on_target_reached.assert_not_called()
    on_below_target.assert_not_called()


def test_decrement_call() -> None:
    """Test the decrement() method when callback is called."""
    on_target_reached = MagicMock()
    on_below_target = MagicMock()
    counter = EventCounter(on_target_reached, on_below_target, target_count=1)
    counter._count = 1
    counter.decrement()
    on_target_reached.assert_not_called()
    on_below_target.assert_called_once_with()


def test_decrement_no_call() -> None:
    """Test the decrement() method when callback is not called."""
    on_target_reached = MagicMock()
    on_below_target = MagicMock()
    counter = EventCounter(on_target_reached, on_below_target, target_count=2)
    counter._count = 1
    counter.decrement()
    on_target_reached.assert_not_called()
    on_below_target.assert_not_called()
