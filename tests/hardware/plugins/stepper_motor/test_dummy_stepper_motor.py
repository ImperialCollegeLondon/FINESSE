"""Tests for DummyStepperMotor."""

from contextlib import nullcontext as does_not_raise
from itertools import chain
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from finesse.config import ANGLE_PRESETS, STEPPER_MOTOR_TOPIC
from finesse.hardware.plugins.stepper_motor.dummy import DummyStepperMotor


@pytest.fixture
def stepper(qtbot) -> DummyStepperMotor:
    """Provides a DummyStepperMotor."""
    return DummyStepperMotor(36)


def test_init(qtbot) -> None:
    """Test DummyStepperMotor's constructor."""
    stepper = DummyStepperMotor(360, 1.0)
    assert stepper._move_end_timer.interval() == 1000
    assert stepper._move_end_timer.isSingleShot()
    assert not stepper._notify_requested
    assert stepper._step == 0


@pytest.mark.parametrize(
    "steps,raises",
    [
        [
            steps,
            pytest.raises(ValueError) if steps <= 0 else does_not_raise(),
        ]
        for steps in range(-5, 5)
    ],
)
def test_init_raises(steps: int, raises: Any, subscribe_mock: MagicMock, qtbot) -> None:
    """Test that constructor raises an error for an invalid step count."""
    with raises:
        stepper = DummyStepperMotor(steps)
        assert stepper._steps_per_rotation == steps


@pytest.mark.parametrize(
    "target,raises",
    [
        [
            target,
            pytest.raises(ValueError)
            if target < 0 or target > 27
            else does_not_raise(),
        ]
        for target in range(-36, 2 * 36)
    ],
)
def test_move_to_number(
    target: int,
    raises: Any,
    stepper: DummyStepperMotor,
    subscribe_mock: MagicMock,
    qtbot,
) -> None:
    """Check move_to, when an angle is given."""
    assert stepper.step == 0

    with patch.object(stepper._move_end_timer, "start") as start_mock:
        with raises:
            stepper.move_to(10.0 * float(target))
            assert stepper.step == target
            start_mock.assert_called_once_with()


# Invalid names for presets. Note that case matters.
BAD_PRESETS = ("", "ZENITH", "kevin", "badger")


@pytest.mark.parametrize(
    "name,raises",
    [
        [
            name,
            pytest.raises(ValueError)
            if name not in ANGLE_PRESETS.keys()
            else does_not_raise(),
        ]
        for name in chain(ANGLE_PRESETS.keys(), BAD_PRESETS)
    ],
)
def test_move_to_preset(
    name: str,
    raises: Any,
    stepper: DummyStepperMotor,
    subscribe_mock: MagicMock,
    qtbot,
) -> None:
    """Check move_to, when a preset name is given."""
    with patch.object(stepper._move_end_timer, "start") as start_mock:
        with raises:
            stepper.move_to(name)
            start_mock.assert_called_once_with()


def test_stop_moving(stepper: DummyStepperMotor, qtbot) -> None:
    """Test the stop_moving() method."""
    with patch.object(stepper._move_end_timer, "stop") as stop_mock:
        with patch.object(stepper, "_on_move_end") as move_end_mock:
            stepper.stop_moving()

            # Check that timer is stopped
            stop_mock.assert_called_once_with()

            # Check that the move end handler is called
            move_end_mock.assert_called_once()


def test_notify_on_stopped(stepper: DummyStepperMotor, qtbot) -> None:
    """Test the notify_on_stopped() method."""
    assert not stepper._notify_requested
    stepper.notify_on_stopped()
    assert stepper._notify_requested


def test_on_move_end_notify(
    stepper: DummyStepperMotor, sendmsg_mock: MagicMock, qtbot
) -> None:
    """Test the _on_move_end() method when notification is requested."""
    stepper.notify_on_stopped()
    assert stepper._notify_requested

    # Trigger move end timer
    stepper._move_end_timer.timeout.emit()

    assert not stepper._notify_requested
    sendmsg_mock.assert_called_once_with(f"device.{STEPPER_MOTOR_TOPIC}.move.end")


def test_on_move_end_no_notify(
    stepper: DummyStepperMotor, sendmsg_mock: MagicMock, qtbot
) -> None:
    """Test the _on_move_end() method when notification is not requested."""
    assert not stepper._notify_requested

    # Trigger move end timer
    stepper._move_end_timer.timeout.emit()

    assert not stepper._notify_requested
    sendmsg_mock.assert_not_called()
