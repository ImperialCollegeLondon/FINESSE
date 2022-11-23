"""Tests for DummyStepperMotor."""
from itertools import chain

import pytest

from finesse.config import ANGLE_PRESETS
from finesse.hardware.dummy_stepper_motor import DummyStepperMotor


@pytest.mark.parametrize("steps", (len(ANGLE_PRESETS), 1000, 10000000))
def test_constructor_good(steps: int) -> None:
    """Check valid arguments to constructor."""
    DummyStepperMotor(steps)


@pytest.mark.parametrize("steps", (-1000000, -1000, *range(-1, len(ANGLE_PRESETS))))
def test_constructor_bad(steps: int) -> None:
    """Check invalid arguments to constructor."""
    with pytest.raises(ValueError):
        DummyStepperMotor(steps)


@pytest.mark.parametrize("target", range(36))
def test_move_to_number_good(target: int) -> None:
    """Check move_to for valid numbers."""
    stepper = DummyStepperMotor(36)
    assert stepper.current_step == 0

    stepper.move_to(10.0 * float(target))
    assert stepper.current_step == target


@pytest.mark.parametrize("target", chain(range(-1, -36, -1), range(36, 2 * 36)))
def test_move_to_number_bad(target: int) -> None:
    """Check move_to for invalid numbers."""
    stepper = DummyStepperMotor(36)
    assert stepper.current_step == 0

    with pytest.raises(ValueError):
        stepper.move_to(10.0 * float(target))


@pytest.mark.parametrize("name", ANGLE_PRESETS)
def test_move_to_preset_good(name: str) -> None:
    """Check move_to for valid preset names."""
    DummyStepperMotor(360).move_to(name)


@pytest.mark.parametrize("name", ("", "ZENITH", "kevin", "badger"))
def test_move_to_preset_bad(name: str) -> None:
    """Check move_to for invalid preset names."""
    with pytest.raises(ValueError):
        DummyStepperMotor(360).move_to(name)
