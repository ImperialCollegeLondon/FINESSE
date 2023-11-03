"""Tests for the HardwareSet class and associated helper functions."""
from importlib import resources
from pathlib import Path
from typing import Any
from unittest.mock import Mock, call, mock_open, patch

import pytest
import yaml

from finesse.gui.hardware_set import hardware_set
from finesse.gui.hardware_set.hardware_set import (
    HardwareSet,
    OpenDeviceArgs,
    load_builtin_hardware_sets,
)

FILE_PATH = Path("test/file.yaml")
NAME = "Test hardware set"


@pytest.mark.parametrize(
    "data,expected",
    (
        # Devices attribute missing
        ({"name": NAME}, HardwareSet(NAME, frozenset(), FILE_PATH, False)),
        # Device given with params
        (
            {
                "name": NAME,
                "devices": {"stepper_motor": {"class_name": "MyStepperMotor"}},
            },
            HardwareSet(
                NAME,
                frozenset((OpenDeviceArgs.create("stepper_motor", "MyStepperMotor"),)),
                FILE_PATH,
                False,
            ),
        ),
        # Device given without params
        (
            {
                "name": NAME,
                "devices": {
                    "stepper_motor": {
                        "class_name": "MyStepperMotor",
                        "params": {"param1": "value1"},
                    }
                },
            },
            HardwareSet(
                NAME,
                frozenset(
                    (
                        OpenDeviceArgs.create(
                            "stepper_motor",
                            "MyStepperMotor",
                            {"param1": "value1"},
                        ),
                    )
                ),
                FILE_PATH,
                False,
            ),
        ),
        # TODO: Test errors
    ),
)
def test_load(data: dict[str, Any], expected: HardwareSet) -> None:
    """Test HardwareSet's static load() method."""
    with patch.object(
        hardware_set.Path,
        "open",
        mock_open(read_data=yaml.dump(data)),
    ):
        result = HardwareSet.load(FILE_PATH, False)
        assert result == expected


@patch.object(HardwareSet, "load")
def test_load_builtin_hardware_sets(load_mock: Mock) -> None:
    """Test the load_builtin_hardware_sets() function."""
    pkg_path = str(resources.files("finesse.gui.hardware_set").joinpath())
    yaml_files = Path(pkg_path).glob("*.yaml")
    list(load_builtin_hardware_sets())  # assume return value is correct
    load_mock.assert_has_calls([call(file, read_only=True) for file in yaml_files])
