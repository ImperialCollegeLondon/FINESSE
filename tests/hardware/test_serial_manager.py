"""Tests for SerialManager."""
from unittest.mock import MagicMock, Mock, patch

import pytest
from pubsub import pub
from serial import SerialException

from finesse.config import DUMMY_DEVICE_PORT
from finesse.hardware.serial_manager import SerialManager


@pytest.fixture
def unsubscribe_mock(monkeypatch) -> MagicMock:
    """Fixture for pub.subscribe."""
    mock = MagicMock()
    monkeypatch.setattr(pub, "unsubscribe", mock)
    return mock


def test_init(subscribe_mock: MagicMock) -> None:
    """Test SerialManager's constructor."""
    manager = SerialManager("my_device", MagicMock(), MagicMock())
    subscribe_mock.assert_any_call(manager._open, "serial.my_device.open")


@patch("finesse.hardware.serial_manager.Serial")
def test_open_real_success(
    serial_mock: Mock, sendmsg_mock: MagicMock, subscribe_mock: MagicMock
) -> None:
    """Test the _open() method with a real serial device that opens successfully."""
    serial = MagicMock()
    serial_mock.return_value = serial

    device_ctor = MagicMock()
    manager = SerialManager("my_device", device_ctor, MagicMock())
    manager._open("COM1", 1234)
    device_ctor.assert_called_once_with(serial)
    subscribe_mock.assert_any_call(manager._close, "serial.my_device.close")
    subscribe_mock.assert_any_call(
        manager._send_close_message, "serial.my_device.error"
    )
    sendmsg_mock.assert_any_call("serial.my_device.opened")


@patch("finesse.hardware.serial_manager.Serial")
def test_open_real_fail(serial_mock: Mock, sendmsg_mock: MagicMock) -> None:
    """Test the _open() method with a real serial device that fails to open."""
    error = SerialException()
    serial_mock.side_effect = error

    manager = SerialManager("my_device", MagicMock(), MagicMock())
    manager._open("COM1", 1234)
    sendmsg_mock.assert_called_once_with("serial.my_device.error", error=error)


def test_open_dummy(sendmsg_mock: MagicMock, subscribe_mock: MagicMock) -> None:
    """Test the _open() method with a dummy serial device."""
    dummy_device_ctor = MagicMock()
    manager = SerialManager("my_device", MagicMock(), dummy_device_ctor)
    manager._open(DUMMY_DEVICE_PORT, 1234)
    dummy_device_ctor.assert_called_once_with()
    subscribe_mock.assert_any_call(manager._close, "serial.my_device.close")
    subscribe_mock.assert_any_call(
        manager._send_close_message, "serial.my_device.error"
    )
    sendmsg_mock.assert_any_call("serial.my_device.opened")


def test_close(unsubscribe_mock: MagicMock) -> None:
    """Test the _close() method."""
    dummy_device_ctor = MagicMock()
    device_mock = MagicMock()
    dummy_device_ctor.return_value = device_mock
    manager = SerialManager("my_device", MagicMock(), dummy_device_ctor)
    manager._open(DUMMY_DEVICE_PORT, 1234)
    manager._close()

    # Check the device was closed
    device_mock.close.assert_called_once_with()

    # Check manager has unsubscribed from future close events
    unsubscribe_mock.assert_any_call(manager._close, "serial.my_device.close")
