"""Tests for SerialControl and associated code."""
from collections import namedtuple
from typing import Any, Sequence
from unittest.mock import MagicMock, Mock, patch

import pytest
from PySide6.QtWidgets import QComboBox, QGridLayout
from pytestqt.qtbot import QtBot

from finesse.gui.serial_view import (
    DUMMY_DEVICE_PORT,
    DeviceControls,
    SerialPortControl,
    get_default_ports,
    get_usb_serial_ports,
)

DEVICE_NAME = "device"
"""The name to use for the mock serial device."""


@pytest.fixture
def device_controls(qtbot: QtBot) -> DeviceControls:
    """A fixture providing a DeviceControls object."""
    ports = ("COM0",)
    baudrates = range(3)
    return DeviceControls(QGridLayout(), 0, DEVICE_NAME, "My device", ports, baudrates)


MockPortInfo = namedtuple("MockPortInfo", "device vid")


@pytest.mark.parametrize(
    "devices,expected",
    (
        # One USB serial device
        (
            [MockPortInfo(device="COM1", vid=1)],
            ["COM1"],
        ),
        # One non-USB serial device
        (
            [MockPortInfo(device="COM1", vid=None)],
            [],
        ),
        # Two USB serial devices, unsorted
        (
            [
                MockPortInfo(device="COM2", vid=1),
                MockPortInfo(device="COM1", vid=1),
            ],
            ["COM1", "COM2"],
        ),
    ),
)
@patch("finesse.gui.serial_view.comports")
def test_get_usb_serial_ports(
    comports_mock: Mock, devices: list[MockPortInfo], expected: list[str]
) -> None:
    """Test the get_usb_serial_ports() function."""
    comports_mock.return_value = devices
    assert get_usb_serial_ports() == expected


@patch("finesse.gui.serial_view.get_usb_serial_ports")
@patch("finesse.gui.serial_view.ALLOW_DUMMY_DEVICES", True)
def test_get_default_ports_dummy(get_usb_mock: Mock) -> None:
    """Test the get_default_ports() function with a dummy device."""
    get_usb_mock.return_value = ["COM1"]
    assert DUMMY_DEVICE_PORT in get_default_ports()


@patch("finesse.gui.serial_view.get_usb_serial_ports")
@patch("finesse.gui.serial_view.ALLOW_DUMMY_DEVICES", False)
def test_get_default_ports_no_dummy(get_usb_mock: Mock) -> None:
    """Test the get_default_ports() function when there should be no dummy devices."""
    get_usb_mock.return_value = ["COM1"]
    assert DUMMY_DEVICE_PORT not in get_default_ports()


def items_equal(combo: QComboBox, values: Sequence[Any]) -> bool:
    """Check that all items of a QComboBox match those in a Sequence."""
    if combo.count() != len(values):
        return False

    items = (combo.itemText(i) for i in range(combo.count()))
    return all(item == str(val) for item, val in zip(items, values))


@patch("finesse.gui.serial_view.QPushButton")
def test_device_controls_init(
    btn_mock: Mock, subscribe_mock: MagicMock, qtbot: QtBot
) -> None:
    """Test DeviceControls' constructor."""
    btn = MagicMock()
    btn_mock.return_value = btn
    ports = ("COM0",)
    baudrates = range(3)

    controls = DeviceControls(
        MagicMock(), 0, DEVICE_NAME, "My device", ports, baudrates
    )
    assert items_equal(controls.ports, ports)
    assert items_equal(controls.baudrates, baudrates)

    btn.clicked.connect.assert_called_once_with(controls._on_open_close_clicked)

    subscribe_mock.assert_any_call(
        controls._set_button_to_close, f"serial.{DEVICE_NAME}.opened"
    )
    subscribe_mock.assert_any_call(
        controls._set_button_to_open, f"serial.{DEVICE_NAME}.close"
    )
    subscribe_mock.assert_any_call(
        controls._show_error_message, f"serial.{DEVICE_NAME}.error"
    )


def test_set_button_to_close(device_controls: DeviceControls) -> None:
    """Test the _set_button_to_close() method."""
    with patch.object(device_controls, "open_close_btn") as btn_mock:
        device_controls._set_button_to_close()
        btn_mock.setText.assert_called_once_with("Close")
        btn_mock.setChecked.assert_called_once_with(True)


def test_set_button_to_open(device_controls: DeviceControls) -> None:
    """Test the _set_button_to_open() method."""
    with patch.object(device_controls, "open_close_btn") as btn_mock:
        device_controls._set_button_to_open()
        btn_mock.setText.assert_called_once_with("Open")
        btn_mock.setChecked.assert_called_once_with(False)


@patch("finesse.gui.serial_view.QMessageBox")
def test_show_error_message(msgbox_mock: Mock, device_controls: DeviceControls) -> None:
    """Test the _show_error_message() method."""
    msgbox = MagicMock()
    msgbox_mock.return_value = msgbox
    device_controls._show_error_message(RuntimeError("hello"))
    msgbox.exec.assert_called_once_with()


def test_on_open_close_clicked(device_controls: DeviceControls, qtbot: QtBot) -> None:
    """Test the open/close button."""
    # Device starts off closed
    assert device_controls.open_close_btn.text() == "Open"
    assert not device_controls.open_close_btn.isChecked()

    with patch.object(device_controls, "_open_device") as open_mock:
        with patch.object(device_controls, "_close_device") as close_mock:
            # Try to open the device
            device_controls._on_open_close_clicked()
            open_mock.assert_called_once()
            close_mock.assert_not_called()

            # Signal that the device opened successfully
            device_controls._set_button_to_close()

            # Check that we can close it again successfully
            open_mock.reset_mock()
            close_mock.reset_mock()
            device_controls._on_open_close_clicked()
            open_mock.assert_not_called()
            close_mock.assert_called_once()


def test_open_device(
    device_controls: DeviceControls,
    qtbot: QtBot,
    sendmsg_mock: MagicMock,
) -> None:
    """Test _open_device()."""
    with patch.object(device_controls.ports, "currentText") as ports_mock:
        ports_mock.return_value = "COM0"
        with patch.object(device_controls.baudrates, "currentText") as baudrates_mock:
            baudrates_mock.return_value = "1234"
            device_controls._open_device()
            sendmsg_mock.assert_any_call(
                f"serial.{DEVICE_NAME}.open", port="COM0", baudrate=1234
            )


def test_close_device(
    device_controls: DeviceControls, qtbot: QtBot, sendmsg_mock: MagicMock
) -> None:
    """Test the _close_device() method."""
    device_controls._close_device()
    sendmsg_mock.assert_any_call(f"serial.{DEVICE_NAME}.close")


@patch("finesse.gui.serial_view.QGridLayout")
@patch("finesse.gui.serial_view.DeviceControls")
def test_serial_port_control_init(
    controls_mock: Mock, grid_mock: Mock, qtbot: QtBot
) -> None:
    """Test SerialPortControl's constructor."""
    # Make the constructor return *this* QGridLayout
    layout = QGridLayout()
    grid_mock.return_value = layout

    devices = ("device1", "device2")
    labels = ("DEVICE1", "DEVICE2")
    avail_ports = ("port1", "port2")
    avail_baudrates = range(2)
    SerialPortControl(devices, labels, avail_ports, avail_baudrates)

    # Check that the appropriate DeviceControls have been created
    for i, (device, label) in enumerate(zip(devices, labels)):
        controls_mock.assert_any_call(
            layout, i, device, label, avail_ports, avail_baudrates
        )
