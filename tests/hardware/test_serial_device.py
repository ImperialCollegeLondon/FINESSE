"""Tests for core serial device code."""
from unittest.mock import MagicMock, Mock, patch

import pytest

from finesse.hardware.serial_device import (
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


@patch("finesse.hardware.serial_device.comports")
def test_get_usb_serial_ports(comports_mock: Mock) -> None:
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

    with patch("finesse.hardware.serial_device._serial_ports", None):
        assert _get_usb_serial_ports() == {
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
