"""Tests for DummyStepperMotor."""
import pytest

from finesse.config import ANGLE_PRESETS
from finesse.hardware.dummy_stepper_motor import DummyStepperMotor


def test_constructor() -> None:
    """Check that the constructor only accepts values in permissible range."""
    with pytest.raises(ValueError):
        DummyStepperMotor(0)

    with pytest.raises(ValueError):
        DummyStepperMotor(-1)

    # Should work
    DummyStepperMotor(len(ANGLE_PRESETS))


def test_move_to_number() -> None:
    """Check that the stepper motor can be moved to valid positions."""
    stepper = DummyStepperMotor(360)

    # Check that we start at step 0
    assert stepper.current_step == 0

    # Out-of-range arguments
    with pytest.raises(ValueError):
        stepper.move_to(-1.0)
    with pytest.raises(ValueError):
        stepper.move_to(360.0)

    # Check that we can move to a valid position
    stepper.move_to(1.0)
    assert stepper.current_step == 1


def test_move_to_preset() -> None:
    """Check that the stepper motor can be moved to valid preset values."""
    stepper = DummyStepperMotor(360)

    # Check that we get an error for invalid presets
    with pytest.raises(ValueError):
        stepper.move_to("MADE UP")

    # Check that we don't get error for valid presets
    for name in ANGLE_PRESETS:
        stepper.move_to(name)
