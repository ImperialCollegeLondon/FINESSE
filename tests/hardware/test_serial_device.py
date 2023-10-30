"""Tests for core serial device code."""
from unittest.mock import MagicMock, Mock, patch

from finesse.hardware.serial_device import _get_usb_serial_ports


@patch("finesse.hardware.serial_device.comports")
def test_get_usb_serial_ports_cached(comports_mock: Mock) -> None:
    """Check that _get_usb_serial_ports() works when results have been cached."""
    serial_ports = ["COM10"]
    with patch("finesse.hardware.serial_device._serial_ports", serial_ports):
        assert _get_usb_serial_ports() == serial_ports
        comports_mock.assert_not_called()


@patch("finesse.hardware.serial_device.comports")
def test_get_usb_serial_ports_not_cached(comports_mock: Mock) -> None:
    """Test _get_usb_serial_ports()."""
    comports = [f"COM{i}" for i in range(3)]
    port_infos = []
    for comport in comports:
        info = MagicMock()
        info.device = comport

        # USB devices should have a vendor ID
        info.vid = 1

        port_infos.append(info)

    # Pretend that this device isn't USB
    port_infos[1].vid = None

    comports_mock.return_value = port_infos

    with patch("finesse.hardware.serial_device._serial_ports", None):
        assert _get_usb_serial_ports() == ["COM0", "COM2"]
