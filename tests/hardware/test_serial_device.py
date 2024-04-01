"""Tests for core serial device code."""

from typing import Any
from unittest.mock import MagicMock, Mock, call, patch

import pytest
from serial import SerialException

from finesse.hardware.serial_device import (
    SerialDevice,
    _create_serial,
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


@pytest.mark.parametrize("refresh", (False, True))
@patch("finesse.hardware.serial_device._get_usb_serial_ports")
@patch("finesse.hardware.serial_device.Serial")
def test_create_serial_success(
    serial_mock: Mock, get_serial_ports_mock: Mock, refresh: bool
) -> None:
    """Test _create_serial() when a connection is successful."""
    serial = MagicMock()
    serial_mock.return_value = serial
    get_serial_ports_mock.return_value = {"name1": "COM1"}
    ret = _create_serial("name1", 1234, refresh)
    assert ret == serial
    serial_mock.assert_called_once_with(port="COM1", baudrate=1234)
    get_serial_ports_mock.assert_called_once_with(refresh)


@pytest.mark.parametrize("refresh", (False, True))
@patch("finesse.hardware.serial_device._get_usb_serial_ports")
@patch("finesse.hardware.serial_device.Serial")
def test_create_serial_fail_no_device(
    serial_mock: Mock, get_serial_ports_mock: Mock, refresh: bool
) -> None:
    """Test _create_serial() when the device is not in the list."""
    get_serial_ports_mock.return_value = {"name1": "COM1"}
    with pytest.raises(SerialException):
        _create_serial("name2", 1234, refresh)


@pytest.mark.parametrize("refresh", (False, True))
@patch("finesse.hardware.serial_device._get_usb_serial_ports")
@patch("finesse.hardware.serial_device.Serial")
def test_create_serial_fail_error(
    serial_mock: Mock, get_serial_ports_mock: Mock, refresh: bool
) -> None:
    """Test _create_serial() when the device is not in the list."""
    serial_mock.side_effect = SerialException
    get_serial_ports_mock.return_value = {"name1": "COM1"}
    with pytest.raises(SerialException):
        _create_serial("name1", 1234, refresh)


@patch("finesse.hardware.serial_device._create_serial")
def test_init_success_first(create_mock: Mock) -> None:
    """Test SerialDevice's constructor when it succeeds the first time."""
    serial = MagicMock()
    create_mock.return_value = serial
    dev = SerialDevice("name1", 1234)
    create_mock.assert_called_once_with("name1", 1234, refresh=False)
    assert dev.serial is serial


@patch("finesse.hardware.serial_device._create_serial")
def test_init_success_second(create_mock: Mock) -> None:
    """Test SerialDevice's constructor when it succeeds the second time."""
    serial = MagicMock()
    create_mock.side_effect = (SerialException, serial)
    dev = SerialDevice("name1", 1234)
    create_mock.assert_has_calls(
        [call("name1", 1234, refresh=refresh) for refresh in (False, True)]
    )
    assert dev.serial is serial


@patch("finesse.hardware.serial_device._create_serial")
def test_init_fail(create_mock: Mock) -> None:
    """Test SerialDevice's constructor when it fails on both attempts."""
    create_mock.side_effect = SerialException
    with pytest.raises(SerialException):
        SerialDevice("name1", 1234)


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
