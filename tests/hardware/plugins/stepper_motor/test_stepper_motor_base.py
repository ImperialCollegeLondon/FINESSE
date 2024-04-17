"""Tests for the StepperMotorBase class."""

from unittest.mock import MagicMock, patch

import pytest

from finesse.hardware.plugins.stepper_motor.stepper_motor_base import StepperMotorBase


class _MockStepperMotor(StepperMotorBase, description="Mock stepper motor"):
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

    def stop_moving(self) -> None:
        pass

    def wait_until_stopped(self, timeout: float | None = None) -> None:
        pass

    def notify_on_stopped(self) -> None:
        pass


@pytest.fixture
def stepper(subscribe_mock: MagicMock) -> StepperMotorBase:
    """Provides a basic StepperMotorBase."""
    return _MockStepperMotor()


def test_init() -> None:
    """Test that StepperMotorBase's constructor subscribes to the right messages."""
    with patch.object(_MockStepperMotor, "subscribe") as subscribe_mock:
        stepper = _MockStepperMotor()
        assert subscribe_mock.call_count == 3
        subscribe_mock.assert_any_call(
            stepper.move_to,
            "move.begin",
        )
        subscribe_mock.assert_any_call(stepper.stop_moving, "stop")
        subscribe_mock.assert_any_call(stepper.notify_on_stopped, "notify_on_stopped")


def test_angle(stepper: _MockStepperMotor) -> None:
    """Test that the angle property works."""
    stepper._steps_per_rotation = 360
    stepper.step = 180
    assert stepper.angle == 180.0

    stepper._steps_per_rotation = 180
    stepper.step = 180
    assert stepper.angle == 360.0
