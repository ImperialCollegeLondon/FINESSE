"""Tests for the StepperMotorBase class."""
from typing import Optional
from unittest.mock import MagicMock

import pytest

from finesse.config import STEPPER_MOTOR_TOPIC
from finesse.hardware.stepper_motor.stepper_motor_base import StepperMotorBase


class _MockStepperMotor(StepperMotorBase):
    def __init__(self) -> None:
        self._steps_per_rotation = 1
        self._step = 0
        super().__init__()

    @property
    def steps_per_rotation(self) -> int:
        return self._steps_per_rotation

    @property
    def is_moving(self) -> bool:
        return False

    @property
    def step(self) -> int | None:
        return self._step

    @step.setter
    def step(self, step: int) -> None:
        self._step = step

    def close(self) -> None:
        pass

    def stop_moving(self) -> None:
        pass

    def wait_until_stopped(self, timeout: Optional[float] = None) -> None:
        pass

    def notify_on_stopped(self) -> None:
        pass


@pytest.fixture
def stepper(error_wrap_mock: MagicMock) -> _MockStepperMotor:
    """Provides a basic StepperMotorBase."""
    return _MockStepperMotor()


def test_init(subscribe_mock: MagicMock) -> None:
    """Test that StepperMotorBase's constructor subscribes to the right messages."""
    stepper = _MockStepperMotor()
    subscribe_mock.assert_any_call(
        stepper._move_to,
        f"serial.{STEPPER_MOTOR_TOPIC}.move.begin",
    )
    subscribe_mock.assert_any_call(
        stepper._stop_moving, f"serial.{STEPPER_MOTOR_TOPIC}.stop"
    )
    subscribe_mock.assert_any_call(
        stepper._notify_on_stopped, f"serial.{STEPPER_MOTOR_TOPIC}.notify_on_stopped"
    )


def test_angle(stepper: _MockStepperMotor) -> None:
    """Test that the angle property works."""
    stepper._steps_per_rotation = 360
    stepper.step = 180
    assert stepper.angle == 180.0

    stepper._steps_per_rotation = 180
    stepper.step = 180
    assert stepper.angle == 360.0


def test_send_error_message(
    sendmsg_mock: MagicMock, stepper: _MockStepperMotor
) -> None:
    """Test the send_error_message() method."""
    error = Exception()
    stepper.send_error_message(error)
    sendmsg_mock.assert_called_once_with(
        f"serial.{STEPPER_MOTOR_TOPIC}.error", error=error
    )
