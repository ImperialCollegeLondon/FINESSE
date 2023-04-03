"""Tests for the StepperMotorBase class."""
from typing import Any, Optional, Sequence
from unittest.mock import MagicMock, patch

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
    def step(self) -> int:
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
def stepper() -> _MockStepperMotor:
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
    subscribe_mock.assert_any_call(
        stepper._request_angle, f"serial.{STEPPER_MOTOR_TOPIC}.request.angle"
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


_ERROR_WRAPPED_FUNCTIONS = (
    ("move_to", (MagicMock(),)),
    ("stop_moving", ()),
    ("notify_on_stopped", ()),
)


@pytest.mark.parametrize("func_name,args", _ERROR_WRAPPED_FUNCTIONS)
def test_error_wrappers_success(
    func_name: str, args: Sequence[Any], stepper: _MockStepperMotor
) -> None:
    """Test that error wrappers work when no errors occur."""
    with patch.object(stepper, func_name) as func_mock:
        getattr(stepper, f"_{func_name}")(*args)
        func_mock.assert_called_once_with(*args)


@pytest.mark.parametrize("func_name,args", _ERROR_WRAPPED_FUNCTIONS)
def test_error_wrappers_fail(
    func_name: str, args: Sequence[Any], stepper: _MockStepperMotor
) -> None:
    """Test that error wrappers work when an exception is raised."""
    with patch.object(stepper, "send_error_message") as send_error_message_mock:
        with patch.object(stepper, func_name) as func_mock:
            error = RuntimeError("hello")
            func_mock.side_effect = error
            getattr(stepper, f"_{func_name}")(*args)
            func_mock.assert_called_once_with(*args)
            send_error_message_mock.assert_called_once_with(error)


def test_request_angle(stepper: _MockStepperMotor, sendmsg_mock: MagicMock) -> None:
    """Test the _request_angle() method."""
    stepper.step = 1
    stepper._steps_per_rotation = 1
    stepper._request_angle()
    sendmsg_mock.assert_called_once_with(
        f"serial.{STEPPER_MOTOR_TOPIC}.response.angle", angle=360.0
    )
