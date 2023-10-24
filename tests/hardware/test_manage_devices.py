"""Tests for manage_devices.py."""
from collections.abc import Iterable
from itertools import product
from unittest.mock import MagicMock, Mock, call, patch

import pytest
from pubsub import pub

from finesse.device_info import DeviceInstanceRef
from finesse.hardware.device import Device
from finesse.hardware.manage_devices import (
    _close_all_devices,
    _close_device,
    _on_device_error,
    _open_device,
    _try_close_device,
)


def test_subscriptions():
    """Check that functions are subscribed to the right messages."""
    assert pub.isSubscribed(_close_device, "device.close")
    assert pub.isSubscribed(_close_all_devices, "window.closed")
    assert pub.isSubscribed(_on_device_error, "device.error")
    assert pub.isSubscribed(_open_device, "device.open")


@pytest.mark.parametrize(
    "name,raise_error", product((None, "device_name"), (False, True))
)
@patch("finesse.hardware.manage_devices.logging")
@patch("finesse.hardware.manage_devices.import_module")
def test_open_device(
    import_mock: Mock,
    logging_mock: Mock,
    sendmsg_mock: MagicMock,
    name: str | None,
    raise_error: bool,
) -> None:
    """Check the _open_device() function."""
    device_mock = MagicMock()
    device_cls_mock = MagicMock()
    device_cls_mock.return_value = device_mock
    if raise_error:
        error = RuntimeError("Error opening device")
        device_cls_mock.side_effect = error

    module_mock = MagicMock()
    module_mock.MyDevice = device_cls_mock
    import_mock.return_value = module_mock
    instance = DeviceInstanceRef("test_type", name)
    params = {"param1": "value1", "param2": "value2"}
    devices_dict: dict[DeviceInstanceRef, Device] = {}

    with patch("finesse.hardware.manage_devices._devices", devices_dict):
        _open_device("some.module.MyDevice", instance, params)
        import_mock.assert_called_once_with("some.module")

        if name:
            device_cls_mock.assert_called_once_with(**params, name=name)
        else:
            device_cls_mock.assert_called_once_with(**params)

        if not raise_error:
            assert devices_dict == {instance: device_mock}
            sendmsg_mock.assert_called_once_with(f"device.opened.{instance.topic}")
            logging_mock.error.assert_not_called()
            logging_mock.warn.assert_not_called()
        else:
            assert not devices_dict
            sendmsg_mock.assert_called_once_with(
                f"device.error.{instance.topic}", instance=instance, error=error
            )
            logging_mock.error.assert_called()


@patch("finesse.hardware.manage_devices.logging")
@patch("finesse.hardware.manage_devices.import_module")
def test_open_device_replace_existing(
    import_mock: Mock, logging_mock: Mock, sendmsg_mock: MagicMock
) -> None:
    """Check that a warning is produced if replacing an existing device instance."""
    device_mock = MagicMock()
    device_cls_mock = MagicMock()
    device_cls_mock.return_value = device_mock
    module_mock = MagicMock()
    module_mock.MyDevice = device_cls_mock
    import_mock.return_value = module_mock
    instance = DeviceInstanceRef("test_type")
    devices_dict: dict[DeviceInstanceRef, Device] = {instance: MagicMock()}
    with patch("finesse.hardware.manage_devices._devices", devices_dict):
        _open_device("some.module.MyDevice", instance, {})
        logging_mock.warn.assert_called()
        assert devices_dict == {instance: device_mock}


def test_try_close_device_success(sendmsg_mock: MagicMock) -> None:
    """Check the _try_close_device() function."""
    base_type_info = MagicMock()
    base_type_info.name = "test"
    device_mock = MagicMock()
    device_mock.name = None
    device_mock.get_device_base_type_info.return_value = base_type_info
    _try_close_device(device_mock)
    device_mock.close.assert_called_once_with()
    sendmsg_mock.assert_called_once_with("device.closed.test")


def test_try_close_device_fail(sendmsg_mock: MagicMock) -> None:
    """Check the _try_close_device() function ignores errors raised during closing."""
    device_mock = MagicMock()
    device_mock.close.side_effect = RuntimeError("Device close failed")
    _try_close_device(device_mock)
    device_mock.close.assert_called_once_with()
    sendmsg_mock.assert_not_called()


def test_close_device() -> None:
    """Check the _close_device() function."""
    device_mock = MagicMock()
    instance_ref = DeviceInstanceRef("test")
    with patch("finesse.hardware.manage_devices._try_close_device") as close_mock:
        with patch(
            "finesse.hardware.manage_devices._devices",
            {instance_ref: device_mock},
        ) as device_dict:
            _close_device(instance_ref)
            close_mock.assert_called_once_with(device_mock)
            assert not device_dict


def test_close_device_no_exist() -> None:
    """Check the _close_device() works when the device doesn't exist."""
    instance_ref = DeviceInstanceRef("test")
    with patch("finesse.hardware.manage_devices._try_close_device") as close_mock:
        _close_device(instance_ref)
        close_mock.assert_not_called()


@pytest.mark.parametrize("raise_error", product((False, True), repeat=2))
def test_close_all_devices(raise_error: Iterable[bool]) -> None:
    """Test the _close_all_devices() function."""
    # Construct a dict of mock devices, whose close() methods raise an error if
    # raise_error is set
    device_dict = {}
    for i, do_raise in enumerate(raise_error):
        device = MagicMock()
        if do_raise:
            device.close.side_effect = RuntimeError("Device close failed")
        device_dict[DeviceInstanceRef(f"test{i}")] = device

    with patch("finesse.hardware.manage_devices._devices", device_dict):
        with patch("finesse.hardware.manage_devices._try_close_device") as close_mock:
            _close_all_devices()

            # Check that the close method was called for every device regardless of
            # whether exceptions were raised along the way
            close_mock.assert_has_calls(
                list(map(call, device_dict.values())), any_order=True
            )

            # Check the device dict was cleared afterwards
            assert not device_dict


@patch("finesse.hardware.manage_devices._close_device")
def test_on_device_error(close_mock: Mock) -> None:
    """Test the _on_device_error() function closes the device instance."""
    instance = DeviceInstanceRef("test")
    _on_device_error(instance, RuntimeError("Error occurred"))
    close_mock.assert_called_once_with(instance)
