"""Tests for the EventCounter class."""
from unittest.mock import MagicMock

from finesse.event_counter import EventCounter


def test_init() -> None:
    """Test EventCounter's constructor."""
    on_target_reached = MagicMock()
    on_below_target = MagicMock()
    counter = EventCounter(1, on_target_reached, on_below_target)
    assert counter._count == 0
    assert counter._target_count == 1
    assert counter._on_target_reached is on_target_reached
    assert counter._on_below_target is on_below_target


def test_increment_call() -> None:
    """Test the increment() method when callback is called."""
    on_target_reached = MagicMock()
    on_below_target = MagicMock()
    counter = EventCounter(1, on_target_reached, on_below_target)
    counter.increment()
    on_target_reached.assert_called_once_with()
    on_below_target.assert_not_called()


def test_increment_no_call() -> None:
    """Test the increment() method when callback is not called."""
    on_target_reached = MagicMock()
    on_below_target = MagicMock()
    counter = EventCounter(2, on_target_reached, on_below_target)
    counter.increment()
    on_target_reached.assert_not_called()
    on_below_target.assert_not_called()


def test_decrement_call() -> None:
    """Test the decrement() method when callback is called."""
    on_target_reached = MagicMock()
    on_below_target = MagicMock()
    counter = EventCounter(1, on_target_reached, on_below_target)
    counter._count = 1
    counter.decrement()
    on_target_reached.assert_not_called()
    on_below_target.assert_called_once_with()


def test_decrement_no_call() -> None:
    """Test the decrement() method when callback is not called."""
    on_target_reached = MagicMock()
    on_below_target = MagicMock()
    counter = EventCounter(2, on_target_reached, on_below_target)
    counter._count = 1
    counter.decrement()
    on_target_reached.assert_not_called()
    on_below_target.assert_not_called()
