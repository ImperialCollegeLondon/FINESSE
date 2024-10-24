"""Configuration for hardware set tests."""

from collections.abc import Sequence
from pathlib import Path

import pytest

from finesse.gui.hardware_set.hardware_set import HardwareSet, OpenDeviceArgs

_HW_SETS = (
    HardwareSet(
        1,
        "Test 1",
        frozenset(
            (
                OpenDeviceArgs.create("stepper_motor", "MyStepperMotor"),
                OpenDeviceArgs.create(
                    "temperature_monitor",
                    "MyTemperatureMonitor",
                    {"param1": "value1"},
                ),
            )
        ),
        Path("path/test.yaml"),
        False,
    ),
    HardwareSet(
        1,
        "Test 2",
        frozenset(
            (
                OpenDeviceArgs.create("stepper_motor", "OtherStepperMotor"),
                OpenDeviceArgs.create("temperature_monitor", "OtherTemperatureMonitor"),
            )
        ),
        Path("path/test2.yaml"),
        False,
    ),
)


@pytest.fixture
def hw_sets() -> Sequence[HardwareSet]:
    """A fixture providing some HardwareSets."""
    return _HW_SETS
