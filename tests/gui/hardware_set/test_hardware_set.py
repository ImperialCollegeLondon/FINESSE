"""Tests for the HardwareSet class and associated helper functions."""
from collections.abc import Sequence
from importlib import resources
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, call, mock_open, patch

import pytest
import yaml
from frozendict import frozendict
from pubsub import pub

from finesse.device_info import DeviceInstanceRef
from finesse.gui.hardware_set import hardware_set
from finesse.gui.hardware_set.hardware_set import (
    HardwareSet,
    OpenDeviceArgs,
    _device_to_plain_data,
    _get_new_hardware_set_path,
    _load_builtin_hardware_sets,
    _load_hardware_sets,
    _save_hardware_set,
    get_hardware_sets,
)

FILE_PATH = Path("test/file.yaml")
NAME = "Test hardware set"


def test_subscriptions() -> None:
    """Check the module-level subscriptions."""
    assert pub.isSubscribed(_save_hardware_set, "hardware_set.add")


@pytest.mark.parametrize(
    "device,expected",
    (
        (
            OpenDeviceArgs(DeviceInstanceRef("base_type"), "my_class"),
            ("base_type", {"class_name": "my_class"}),
        ),
        (
            OpenDeviceArgs(
                DeviceInstanceRef("base_type"), "my_class", frozendict(a=1, b="hello")
            ),
            ("base_type", {"class_name": "my_class", "params": {"a": 1, "b": "hello"}}),
        ),
    ),
)
def test_device_to_plain_data(device: OpenDeviceArgs, expected: dict[str, Any]) -> None:
    """Test _device_to_plain_data()."""
    assert _device_to_plain_data(device) == expected


@patch("finesse.gui.hardware_set.hardware_set._device_to_plain_data")
@patch("finesse.gui.hardware_set.hardware_set.yaml.dump")
def test_hardware_set_save(dump_mock: Mock, to_plain_mock: Mock) -> None:
    """Test HardwareSet's save() method."""
    file_path = MagicMock()
    devices = (
        OpenDeviceArgs(DeviceInstanceRef(f"base_type{i}"), f"my_class{i}")
        for i in range(2)
    )
    to_plain_mock.side_effect = ((f"key{i}", i) for i in range(2))
    hw_set = HardwareSet(NAME, frozenset(devices), FILE_PATH, False)
    hw_set.save(file_path)
    expected = {"name": NAME, "devices": {"key0": 0, "key1": 1}}
    assert dump_mock.call_count == 1
    assert dump_mock.mock_calls[0].args[0] == expected


def test_hardware_set_save_and_load(tmp_path: Path) -> None:
    """Test that saved files are loadable."""
    devices = (
        OpenDeviceArgs(DeviceInstanceRef(f"base_type{i}"), f"my_class{i}")
        for i in range(2)
    )
    save_path = tmp_path / "file.yaml"
    hw_set1 = HardwareSet(NAME, frozenset(devices), save_path, False)
    hw_set1.save(save_path)
    hw_set2 = HardwareSet.load(save_path, False)
    assert hw_set1 == hw_set2


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


@pytest.mark.parametrize(
    "to_create,expected_file_name",
    (
        ((), "file.yaml"),
        (("file.yaml",), "file_2.yaml"),
        (("file.yaml", "file_2.yaml"), ("file_3.yaml")),
    ),
)
def test_get_new_hardware_set_path(
    to_create: Sequence[str], expected_file_name: str, tmp_path: Path
) -> None:
    """Test _get_new_hardware_set_path()."""
    output_dir = tmp_path / "sub"

    # Create files
    output_dir.mkdir()
    for file_name in to_create:
        open(output_dir / file_name, "w").close()

    assert (
        _get_new_hardware_set_path("file", output_dir)
        == output_dir / expected_file_name
    )


def test_get_new_hardware_set_path_creates_dir(tmp_path: Path) -> None:
    """Test that _get_new_hardware_set_path() creates the target directory."""
    output_dir = tmp_path / "sub"
    _get_new_hardware_set_path("file", output_dir)
    assert output_dir.exists()


@patch("finesse.gui.hardware_set.hardware_set._get_new_hardware_set_path")
@patch("finesse.gui.hardware_set.hardware_set.show_error_message")
def test_save_hardware_set_success(
    error_message_mock: Mock, get_path_mock: Mock, sendmsg_mock: MagicMock
) -> None:
    """Test _save_hardware_set()."""
    in_path = Path("dir1/file.yaml")
    out_path = Path("dir2/file.yaml")
    hw_set = MagicMock()
    hw_set.name = NAME
    hw_set.file_path = in_path
    hw_set.devices = HW_SETS[0].devices
    hw_set.built_in = False
    get_path_mock.return_value = out_path
    hw_sets: list = []
    with patch("finesse.gui.hardware_set.hardware_set._hw_sets", hw_sets):
        hw_set_new = HardwareSet(NAME, HW_SETS[0].devices, out_path, built_in=False)
        _save_hardware_set(hw_set)
        get_path_mock.assert_called_once_with(in_path.stem)
        hw_set.save.assert_called_once_with(out_path)
        error_message_mock.assert_not_called()
        assert hw_sets == [hw_set_new]  # NB: Should be sorted but we don't check this
        sendmsg_mock.assert_called_once_with("hardware_set.added", hw_set=hw_set_new)


@patch("finesse.gui.hardware_set.hardware_set._get_new_hardware_set_path")
@patch("finesse.gui.hardware_set.hardware_set.show_error_message")
def test_save_hardware_set_fail(
    error_message_mock: Mock, get_path_mock: Mock, sendmsg_mock: MagicMock
) -> None:
    """Test _save_hardware_set()."""
    in_path = Path("dir1/file.yaml")
    out_path = Path("dir2/file.yaml")
    hw_set = MagicMock()
    hw_set.file_path = in_path
    hw_set.save.side_effect = RuntimeError
    get_path_mock.return_value = out_path
    hw_sets: list = []
    with patch("finesse.gui.hardware_set.hardware_set._hw_sets", hw_sets):
        _save_hardware_set(hw_set)
        get_path_mock.assert_called_once_with(in_path.stem)
        hw_set.save.assert_called_once_with(out_path)
        error_message_mock.assert_called_once()
        sendmsg_mock.assert_not_called()


@patch.object(HardwareSet, "load")
def test_load_builtin_hardware_sets(load_mock: Mock) -> None:
    """Test the load_builtin_hardware_sets() function."""
    pkg_path = str(resources.files("finesse.gui.hardware_set").joinpath())
    yaml_files = Path(pkg_path).glob("*.yaml")
    list(_load_builtin_hardware_sets())  # assume return value is correct
    load_mock.assert_has_calls([call(file, built_in=True) for file in yaml_files])


@patch("finesse.gui.hardware_set.hardware_set._load_builtin_hardware_sets")
def test_load_hardware_sets(load_builtin_mock: Mock) -> None:
    """Test _load_hardware_sets()."""
    hw_sets: list[int] = []
    with patch("finesse.gui.hardware_set.hardware_set._hw_sets", hw_sets):
        load_builtin_mock.return_value = (1, 0)  # deliberately unsorted
        _load_hardware_sets()
        assert hw_sets == [0, 1]


def test_get_hardware_sets() -> None:
    """Test the get_hardware_sets() method."""
    hw_sets = list(range(2))
    with patch("finesse.gui.hardware_set.hardware_set._hw_sets", hw_sets):
        assert list(get_hardware_sets()) == hw_sets
