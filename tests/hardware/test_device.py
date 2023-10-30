"""Tests for device.py."""
from collections.abc import Callable, Sequence
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

from finesse.device_info import DeviceParameter, DeviceTypeInfo
from finesse.hardware.device import AbstractDevice, Device, get_device_types


class _MockBaseClass(
    Device, is_base_type=True, name="mock", description="Mock base class"
):
    pass


class _MockDevice(_MockBaseClass, description="Mock device"):
    pass


@pytest.fixture
def device():
    """A fixture for a mock device."""
    return _MockDevice()


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


def _wrapped_func_error_test(device: Device, wrapper: Callable, *args) -> None:
    has_run = False

    def raise_error():
        nonlocal has_run
        has_run = True
        raise RuntimeError()

    with patch.object(device, "send_error_message") as error_mock:
        wrapped_func = wrapper(raise_error, *args)
        wrapped_func()
        assert has_run
        error_mock.assert_called_once()


def test_device_pubsub_errors_success(device: Device) -> None:
    """Test Device's pubsub_errors() method when no exception is raised."""
    has_run = False

    def noop():
        nonlocal has_run
        has_run = True

    with patch.object(device, "send_error_message") as error_mock:
        wrapped_func = device.pubsub_errors(noop)
        wrapped_func()
        assert has_run
        error_mock.assert_not_called()


def test_device_pubsub_errors_fail(device: Device) -> None:
    """Test Device's pubsub_errors() method when an exception is raised."""
    _wrapped_func_error_test(device, device.pubsub_errors)


@pytest.mark.parametrize(
    "return_val,kwarg_names,forwarded_args",
    (
        (None, (), ()),
        (
            0,
            ("value",),
            (0,),
        ),
        ((0, 1), ("val1", "val2"), (0, 1)),
    ),
)
def test_device_pubsub_broadcast_success(
    device: Device,
    sendmsg_mock: MagicMock,
    return_val: Any,
    kwarg_names: Sequence[str],
    forwarded_args: Sequence[Any],
) -> None:
    """Test Device's pubsub_broadcast() method."""
    has_run = False

    def noop():
        nonlocal has_run
        has_run = True
        return return_val

    with patch.object(device, "send_error_message") as error_mock:
        wrapped_func = device.pubsub_broadcast(noop, "success", *kwarg_names)
        wrapped_func()
        assert has_run
        sendmsg_mock.assert_called_once_with(
            "device.mock.success", **dict(zip(kwarg_names, forwarded_args))
        )
        error_mock.assert_not_called()


def test_device_pubsub_broadcast_fail(device: Device) -> None:
    """Test Device's pubsub_broadcast() method when an exception is raised."""
    _wrapped_func_error_test(device, device.pubsub_broadcast, "success")


def test_device_send_error_message(device: Device, sendmsg_mock: MagicMock) -> None:
    """Test Device's send_error_message() method."""
    error = RuntimeError()
    device.send_error_message(error)
    sendmsg_mock.assert_called_once_with(
        "device.error.mock", instance=device.get_instance_ref(), error=error
    )


def _device_subscribe_test(
    device: Device, subscribe_mock: MagicMock, wrapper_name: str, *args
) -> None:
    assert len(device._subscriptions) == 0

    def noop():
        pass

    with patch.object(device, wrapper_name) as wrapper_mock:
        wrapped = MagicMock()
        wrapper_mock.return_value = wrapped
        device.subscribe(noop, "message", *args)
        wrapper_mock.assert_called_once_with(noop, *args)
        sub_args = (wrapped, "device.mock.message")
        assert device._subscriptions == [sub_args]
        subscribe_mock.assert_called_once_with(*sub_args)


def test_device_subscribe_errors_only(
    device: Device, subscribe_mock: MagicMock
) -> None:
    """Test the subscribe() method for when a message is only sent in case of error."""
    _device_subscribe_test(device, subscribe_mock, "pubsub_errors")


def test_device_subscribe_broadcast(device: Device, subscribe_mock: MagicMock) -> None:
    """Test the subscribe() method with a message sent for error and success."""
    _device_subscribe_test(device, subscribe_mock, "pubsub_broadcast", "suffix", "name")


def test_device_close(device: Device, unsubscribe_mock: MagicMock) -> None:
    """Test the close() method."""
    func = MagicMock()
    my_topic = "topic"
    device._subscriptions.append((func, my_topic))
    device.close()
    assert unsubscribe_mock.call_count == 1
    unsubscribe_mock.assert_called_once_with(func, my_topic)
