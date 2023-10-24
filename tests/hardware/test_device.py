"""Tests for device.py."""
from unittest.mock import MagicMock, Mock, patch

from finesse.device_info import DeviceParameter, DeviceTypeInfo
from finesse.hardware.device import AbstractDevice, get_device_types


@patch("finesse.hardware.device.load_all_plugins")
def test_get_device_types(load_plugins_mock: Mock) -> None:
    """Test the get_device_types() function."""
    # NB: Deliberately not in alphabetical order as the result should be sorted
    base_type_names = ("BaseTypeB", "BaseTypeA")
    base_types_info = []
    base_types = []
    for desc in base_type_names:
        info_mock = MagicMock()
        info_mock.description = desc
        base_types_info.append(info_mock)
        type_mock = MagicMock()
        type_mock.get_device_base_type_info.return_value = info_mock
        base_types.append(type_mock)

    # As above, this is a set in the actual implementation
    device_types_info = []
    device_types = []
    for i, base_type_info in enumerate([*base_types_info, base_types_info[0]]):
        # As above, we want to check that the device types are sorted by name
        info_mock = MagicMock()
        info_mock.description = f"Device{len(base_types)-i}"
        device_types_info.append(info_mock)

        device_mock = MagicMock()
        device_mock.get_device_base_type_info.return_value = base_type_info
        device_mock.get_device_type_info.return_value = info_mock
        device_types.append(device_mock)

    with patch("finesse.hardware.device._base_types", base_types):
        with patch("finesse.hardware.device._device_types", device_types):
            device_types_out = get_device_types()
            load_plugins_mock.assert_called_once_with()

            keys = list(device_types_out.keys())

            # Check that keys are present and sorted
            assert [key.description for key in keys] == [
                "BaseTypeA",
                "BaseTypeB",
            ]

            def get_names(idx):
                return [t.description for t in device_types_out[keys[idx]]]

            # Check that device types are all present and sorted by name
            assert get_names(0) == ["Device1"]
            assert get_names(1) == ["Device0", "Device2"]


def test_abstract_device_device_parameters() -> None:
    """Test AbstractDevice's device parameter classmethods."""

    class MyDevice(AbstractDevice):
        pass

    assert MyDevice.get_device_parameters() == []
    param = DeviceParameter("param1", ["a", "b"])
    MyDevice.add_device_parameters(param)
    assert MyDevice.get_device_parameters() == [param]


def test_abstract_device_get_device_base_type_info() -> None:
    """Test the get_device_base_type_info() classmethod."""

    class MyDevice(AbstractDevice):
        _device_base_type_info = "INFO"  # type: ignore

    assert MyDevice.get_device_base_type_info() == "INFO"


def test_abstract_device_get_device_type_info() -> None:
    """Test the get_device_type_info() classmethod."""

    class MyDevice(AbstractDevice):
        _device_description = "DESCRIPTION"

    param = DeviceParameter("param1", ["a", "b"])
    MyDevice.add_device_parameters(param)

    assert MyDevice.get_device_type_info() == DeviceTypeInfo(
        "DESCRIPTION", [param], f"{MyDevice.__module__}.MyDevice"
    )
