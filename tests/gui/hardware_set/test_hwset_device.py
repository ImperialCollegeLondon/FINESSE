"""Test the helper functions in device_connection.py."""

from unittest.mock import MagicMock

from finesse.device_info import DeviceInstanceRef
from finesse.gui.hardware_set.device import close_device, open_device


def test_open_device(sendmsg_mock: MagicMock) -> None:
    """Test open_device()."""
    class_name = "MyDevice"
    instance = DeviceInstanceRef("my_base_type")
    params = {"my_param": "my_value"}
    open_device(class_name, instance, params)
    sendmsg_mock.assert_called_once_with(
        "device.open", class_name=class_name, instance=instance, params=params
    )


def test_close_device(sendmsg_mock: MagicMock) -> None:
    """Test close_device()."""
    instance = DeviceInstanceRef("my_base_type")
    close_device(instance)
    sendmsg_mock.assert_called_once_with("device.close", instance=instance)
