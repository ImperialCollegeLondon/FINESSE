"""Tests for core serial device code."""
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest
from serial import SerialException

from finesse.hardware.serial_device import (
    SerialDevice,
    _get_port_number,
    _get_usb_serial_ports,
    _port_info_to_str,
)


@patch("finesse.hardware.serial_device.comports")
def test_get_usb_serial_ports_cached(comports_mock: Mock) -> None:
    """Check that _get_usb_serial_ports() works when results have been cached."""
    serial_ports = {_port_info_to_str(1, 2, 0): "COM1"}
    with patch("finesse.hardware.serial_device._serial_ports", serial_ports):
        assert _get_usb_serial_ports() == serial_ports
        comports_mock.assert_not_called()


@pytest.mark.parametrize(
    "refresh,serial_ports", ((False, None), (True, {"key": "value"}))
)
@patch("finesse.hardware.serial_device.comports")
def test_get_usb_serial_ports(
    comports_mock: Mock, refresh: bool, serial_ports: Any
) -> None:
    """Test _get_usb_serial_ports()."""
    VID = 1
    PID = 2

    ports = []
    for comport in ("COM3", "COM2", "COM1"):
        info = MagicMock()
        info.device = comport

        info.vid = VID
        info.pid = PID

        ports.append(info)

    # Pretend that this device isn't USB
    ports[1].vid = None

    comports_mock.return_value = ports

    with patch("finesse.hardware.serial_device._serial_ports", serial_ports):
        assert _get_usb_serial_ports(refresh) == {
            _port_info_to_str(VID, PID, 0): "COM1",
            _port_info_to_str(VID, PID, 1): "COM3",
        }


@pytest.mark.parametrize(
    "port,number",
    (
        (f"{prefix}{number}", number)
        for number in (1, 2, 10)
        for prefix in ("COM", "/dev/ttyUSB")
    ),
)
def test_get_port_number(port: str, number: int) -> None:
    """Test _get_port_number()."""
    assert _get_port_number(port) == number


def test_get_port_number_bad() -> None:
    """Test _get_port_number() when a bad value is provided."""
    with pytest.raises(ValueError):
        _get_port_number("NO_NUMBER")


@patch("finesse.hardware.serial_device._serial_ports", {"name1": "COM1"})
@patch("finesse.hardware.serial_device.Serial")
def test_init(serial_mock: Mock) -> None:
    """Test SerialDevice's constructor."""
    serial = MagicMock()
    serial_mock.return_value = serial
    dev = SerialDevice("name1", 1234)
    serial_mock.assert_called_once_with(port="COM1", baudrate=1234)
    assert dev.serial is serial


@patch(
    "finesse.hardware.serial_device._get_usb_serial_ports",
    return_value={"name2": "COM2"},
)
@patch("finesse.hardware.serial_device._serial_ports", {"name1": "COM1"})
@patch("finesse.hardware.serial_device.Serial")
def test_init_refresh_succeed(serial_mock: Mock, get_ports_mock: Mock) -> None:
    """Test SerialDevice's constructor succeeds after refreshing ports."""
    serial = MagicMock()
    serial_mock.return_value = serial
    dev = SerialDevice("name2", 1234)
    serial_mock.assert_called_once_with(port="COM2", baudrate=1234)
    assert dev.serial is serial


@patch(
    "finesse.hardware.serial_device._get_usb_serial_ports",
    return_value={"name2": "COM2"},
)
@patch("finesse.hardware.serial_device._serial_ports", {"name1": "COM1"})
@patch("finesse.hardware.serial_device.Serial")
def test_init_refresh_fail(serial_mock: Mock, get_ports_mock: Mock) -> None:
    """Test SerialDevice's constructor raises an exception if the port isn't found."""
    with pytest.raises(SerialException):
        SerialDevice("name3", 1234)


@patch("finesse.hardware.serial_device._serial_ports", {"name1": "COM1"})
@patch("finesse.hardware.serial_device.Serial")
def test_close(serial_mock: Mock) -> None:
    """Test SerialDevice's close() method."""
    serial = MagicMock()
    serial_mock.return_value = serial
    dev = SerialDevice("name1", 1234)
    serial_mock.assert_called_once_with(port="COM1", baudrate=1234)

    dev.close()
    serial.close.assert_called_once_with()
