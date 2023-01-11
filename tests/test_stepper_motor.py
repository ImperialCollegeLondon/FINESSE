"""Tests for DummyStepperMotor."""
from contextlib import nullcontext as does_not_raise
from itertools import chain
from typing import Any

import pytest

from finesse.config import ANGLE_PRESETS
from finesse.hardware.dummy_stepper_motor import DummyStepperMotor


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
def test_constructor(steps: int, raises: Any) -> None:
    """Check arguments to constructor."""
    with raises:
        DummyStepperMotor(steps)


@pytest.mark.parametrize(
    "target,raises",
    [
        [
            target,
            pytest.raises(ValueError)
            if target < 0 or target >= 36
            else does_not_raise(),
        ]
        for target in range(-36, 2 * 36)
    ],
)
def test_move_to_number(target: int, raises: Any) -> None:
    """Check move_to, when an angle is given."""
    stepper = DummyStepperMotor(36)
    assert stepper.current_step == 0

    with raises:
        stepper.move_to(10.0 * float(target))
        assert stepper.current_step == target


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
def test_move_to_preset(name: str, raises: Any) -> None:
    """Check move_to, when a preset name is given."""
    with raises:
        DummyStepperMotor(360).move_to(name)
