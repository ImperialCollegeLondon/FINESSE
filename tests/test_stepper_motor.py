"""Tests for DummyStepperMotor."""
import pytest

from finesse.hardware.dummy_stepper_motor import DummyStepperMotor


def test_constructor() -> None:
    """Check that the constructor only accepts values in permissible range."""
    with pytest.raises(ValueError):
        DummyStepperMotor(0)

    with pytest.raises(ValueError):
        DummyStepperMotor(-1)

    # Should work
    DummyStepperMotor(1)


def test_move_to() -> None:
    """Check that the stepper motor can be moved to valid positions."""
    stepper = DummyStepperMotor(2)

    # Check that we start at step 0
    assert stepper.current_step == 0

    # Out-of-range arguments
    with pytest.raises(ValueError):
        stepper.move_to(-1)
    with pytest.raises(ValueError):
        stepper.move_to(2)

    # Check that we can move to a valid position
    stepper.move_to(1)
    assert stepper.current_step == 1
