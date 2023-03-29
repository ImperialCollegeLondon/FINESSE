"""Tests for SerialManager."""
from unittest.mock import MagicMock, Mock, patch

import pytest
from pubsub import pub
from serial import SerialException

from finesse.config import DUMMY_DEVICE_PORT
from finesse.hardware.serial_manager import SerialManager, make_device_factory


@pytest.fixture
def unsubscribe_mock(monkeypatch) -> MagicMock:
    """Fixture for pub.subscribe."""
    mock = MagicMock()
    monkeypatch.setattr(pub, "unsubscribe", mock)
    return mock


@patch("finesse.hardware.serial_manager.Serial")
def test_make_device_factory_real(serial_mock: Mock) -> None:
    """Test the make_device_factory() function when constructing a real device."""
    serial = MagicMock()
    serial_mock.return_value = serial

    device_factory = MagicMock()
    device_factory.return_value = "MAGIC"
    create_device = make_device_factory(device_factory, MagicMock())
    assert create_device("COM1", 1234) == "MAGIC"
    serial_mock.assert_called_once_with("COM1", 1234)
    device_factory.assert_called_once_with(serial)


def test_make_device_factory_dummy() -> None:
    """Test the make_device_factory() function when constructing a dummy device."""
    dummy_device_factory = MagicMock()
    dummy_device_factory.return_value = "MAGIC"
    create_device = make_device_factory(MagicMock(), dummy_device_factory)
    assert create_device(DUMMY_DEVICE_PORT, 1234) == "MAGIC"
    dummy_device_factory.assert_called_once_with()


def test_init(subscribe_mock: MagicMock) -> None:
    """Test SerialManager's constructor."""
    device_factory = MagicMock()
    manager = SerialManager("my_device", device_factory)
    assert manager.device_factory == device_factory
    subscribe_mock.assert_any_call(manager._open, "serial.my_device.open")


def test_open_real_success(sendmsg_mock: MagicMock, subscribe_mock: MagicMock) -> None:
    """Test the _open() method with a device that opens successfully."""
    device_factory = MagicMock()
    manager = SerialManager("my_device", device_factory)
    manager._open("COM1", 1234)
    device_factory.assert_called_once_with("COM1", 1234)
    subscribe_mock.assert_any_call(manager._close, "serial.my_device.close")
    subscribe_mock.assert_any_call(
        manager._send_close_message, "serial.my_device.error"
    )
    sendmsg_mock.assert_any_call("serial.my_device.opened")


def test_open_real_fail(sendmsg_mock: MagicMock) -> None:
    """Test the _open() method with a device that fails to open."""
    device_factory = MagicMock()
    error = SerialException()
    device_factory.side_effect = error

    manager = SerialManager("my_device", device_factory)
    manager._open("COM1", 1234)
    sendmsg_mock.assert_called_once_with("serial.my_device.error", error=error)


def test_close(unsubscribe_mock: MagicMock) -> None:
    """Test the _close() method."""
    device_factory = MagicMock()
    device = MagicMock()
    device_factory.return_value = device
    manager = SerialManager("my_device", device_factory)
    manager._open(DUMMY_DEVICE_PORT, 1234)
    manager._close()

    # Check the device was closed
    device.close.assert_called_once_with()

    # Check manager has unsubscribed from future close events
    unsubscribe_mock.assert_any_call(manager._close, "serial.my_device.close")
