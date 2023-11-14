"""Tests for the HardwareSetsControl class."""
from collections.abc import Sequence
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from unittest.mock import MagicMock, Mock, PropertyMock, call, patch

import pytest

from finesse.gui.hardware_set.hardware_set import HardwareSet, OpenDeviceArgs
from finesse.gui.hardware_set.hardware_sets_view import HardwareSetsControl

HW_SETS = [
    HardwareSet(
        "Test 1",
        frozenset(
            (
                OpenDeviceArgs.create("stepper_motor", "MyStepperMotor"),
                OpenDeviceArgs.create(
                    "temperature_monitor",
                    "MyTemperatureMonitor",
                    {"param1": "value1"},
                ),
            )
        ),
        Path("path/test.yaml"),
        False,
    ),
    HardwareSet(
        "Test 2",
        frozenset(
            (
                OpenDeviceArgs.create("stepper_motor", "OtherStepperMotor"),
                OpenDeviceArgs.create("temperature_monitor", "OtherTemperatureMonitor"),
            )
        ),
        Path("path/test2.yaml"),
        False,
    ),
]


@pytest.fixture
@patch("finesse.gui.hardware_set.hardware_sets_view.load_builtin_hardware_sets")
def hw_sets(
    load_hw_sets_mock: Mock, sendmsg_mock: MagicMock, subscribe_mock: MagicMock, qtbot
) -> HardwareSetsControl:
    """A fixture for the control."""
    load_hw_sets_mock.return_value = HW_SETS
    return HardwareSetsControl()


@pytest.mark.parametrize("selected_hw_set", (hw_set.name for hw_set in HW_SETS))
@patch("finesse.gui.hardware_set.hardware_sets_view.load_builtin_hardware_sets")
def test_init(
    load_hw_sets_mock: Mock, selected_hw_set: str, subscribe_mock: MagicMock, qtbot
) -> None:
    """Test the constructor."""
    with patch("finesse.gui.hardware_set.hardware_sets_view.settings") as settings_mock:
        settings_mock.value.return_value = selected_hw_set
        load_hw_sets_mock.return_value = HW_SETS
        hw_sets = HardwareSetsControl()
        settings_mock.value.assert_called_once_with("hardware_set/selected")
        assert hw_sets._hardware_sets_combo.count() == 2
        assert hw_sets._hardware_sets_combo.currentText() == selected_hw_set
        assert hw_sets._connect_btn.isEnabled()
        assert not hw_sets._disconnect_btn.isEnabled()

        subscribe_mock.assert_has_calls(
            [
                call(hw_sets._on_device_opened, "device.opening"),
                call(hw_sets._on_device_closed, "device.closed"),
            ]
        )


def test_add_hardware_set(hw_sets: HardwareSetsControl, qtbot) -> None:
    """Test the add_hardware_set() method."""
    with patch.object(hw_sets._hardware_sets_combo, "addItem") as add_mock:
        hw_set = MagicMock()
        hw_set.name = "New name"
        hw_sets._add_hardware_set(hw_set)
        add_mock.assert_called_once_with("New name", hw_set)

        # Check a number is appended if the name already exists
        add_mock.reset_mock()
        hw_set2 = MagicMock()
        hw_set2.name = "Test 1"
        hw_sets._add_hardware_set(hw_set2)
        add_mock.assert_called_once_with("Test 1 (2)", hw_set2)

    # Check that the number increments
    hw_sets._hardware_sets_combo.addItem("Test 1 (2)")
    with patch.object(hw_sets._hardware_sets_combo, "addItem") as add_mock:
        add_mock.reset_mock()
        hw_set3 = MagicMock()
        hw_set3.name = "Test 1"
        hw_sets._add_hardware_set(hw_set3)
        add_mock.assert_called_once_with("Test 1 (3)", hw_set3)


DEVICES = [
    OpenDeviceArgs.create(f"type{i}", f"class{i}", {"my_param": "my_value"})
    for i in range(2)
]


def _get_devices(indexes: Sequence[int]) -> set[OpenDeviceArgs]:
    return {DEVICES[idx] for idx in indexes}


@pytest.mark.parametrize(
    "connect_enabled,disconnect_enabled,connected_devices,hardware_set",
    (
        (True, False, (), range(2)),
        (False, True, range(2), range(2)),
        (True, True, (1,), range(2)),
        (False, False, (), ()),
    ),
)
def test_update_control_state(
    connect_enabled: bool,
    disconnect_enabled: bool,
    connected_devices: Sequence[int],
    hardware_set: Sequence[int],
    hw_sets: HardwareSetsControl,
    sendmsg_mock: MagicMock,
    qtbot,
) -> None:
    """Test the _update_control_state() method."""
    with patch(
        "finesse.gui.hardware_set.hardware_sets_view"
        ".HardwareSetsControl.current_hardware_set",
        new_callable=PropertyMock,
    ) as hw_set_mock:
        hw_set_mock.return_value = _get_devices(hardware_set)
        with patch.object(
            hw_sets, "_connected_devices", _get_devices(connected_devices)
        ):
            with patch.object(
                hw_sets._connect_btn, "setEnabled"
            ) as connect_enable_mock:
                with patch.object(
                    hw_sets._disconnect_btn, "setEnabled"
                ) as disconnect_enable_mock:
                    hw_sets._update_control_state()
                    connect_enable_mock.assert_called_once_with(connect_enabled)
                    disconnect_enable_mock.assert_called_once_with(disconnect_enabled)


@pytest.mark.parametrize(
    "connected_devices,hardware_set,open_called",
    (((), range(2), range(2)), (range(2), range(2), ()), ((0,), range(2), (1,))),
)
@patch("finesse.gui.hardware_set.hardware_sets_view.settings")
@patch("finesse.gui.hardware_set.hardware_set.open_device")
def test_connect_btn(
    open_mock: Mock,
    settings_mock: Mock,
    connected_devices: Sequence[int],
    hardware_set: Sequence[int],
    open_called: Sequence[int],
    hw_sets: HardwareSetsControl,
    qtbot,
) -> None:
    """Test the connect button."""
    with patch(
        "finesse.gui.hardware_set.hardware_sets_view"
        ".HardwareSetsControl.current_hardware_set",
        new_callable=PropertyMock,
    ) as hw_set_mock:
        hw_set_mock.return_value = _get_devices(hardware_set)
        with patch.object(
            hw_sets, "_connected_devices", _get_devices(connected_devices)
        ):
            hw_sets._connect_btn.click()

            open_mock.assert_has_calls(
                list(
                    call(dev.class_name, dev.instance, dev.params)
                    for dev in _get_devices(open_called)
                ),
                any_order=True,
            )

            settings_mock.setValue.assert_called_once_with(
                "hardware_set/selected", "Test 1"
            )


@patch("finesse.gui.hardware_set.hardware_set.close_device")
def test_disconnect_button(
    close_mock: Mock, hw_sets: HardwareSetsControl, qtbot
) -> None:
    """Test the disconnect button."""
    with patch.object(hw_sets, "_update_control_state") as update_mock:
        with patch.object(hw_sets, "_connected_devices", DEVICES):
            hw_sets._disconnect_btn.setEnabled(True)
            hw_sets._disconnect_btn.click()
            close_mock.assert_has_calls([call(device.instance) for device in DEVICES])
            update_mock.assert_called_once_with()


@patch("finesse.gui.hardware_set.hardware_sets_view.settings")
def test_on_device_opened(
    settings_mock: Mock, hw_sets: HardwareSetsControl, qtbot
) -> None:
    """Test the _on_device_opened() method."""
    device = DEVICES[0]
    assert not hw_sets._connected_devices
    with patch.object(hw_sets, "_update_control_state") as update_mock:
        hw_sets._on_device_opened(
            instance=device.instance, class_name=device.class_name, params=device.params
        )
        assert hw_sets._connected_devices == {device}
        update_mock.assert_called_once_with()
        settings_mock.setValue.assert_has_calls(
            [
                call(f"device/type/{device.instance.topic}", device.class_name),
                call(f"device/params/{device.class_name}", device.params),
            ]
        )


def test_on_device_closed(hw_sets: HardwareSetsControl, qtbot) -> None:
    """Test the _on_device_closed() method."""
    device = DEVICES[0]
    assert not hw_sets._connected_devices
    with patch.object(hw_sets, "_update_control_state") as update_mock:
        hw_sets._connected_devices.add(device)
        hw_sets._on_device_closed(device.instance)
        assert not hw_sets._connected_devices
        update_mock.assert_called_once_with()


def test_on_device_closed_not_found(hw_sets: HardwareSetsControl, qtbot) -> None:
    """Test that _on_device_closed() does not raise an error if device is not found."""
    device = DEVICES[0]
    assert not hw_sets._connected_devices
    with does_not_raise():
        hw_sets._on_device_closed(device.instance)


def test_show_manage_devices_dialog(hw_sets: HardwareSetsControl, qtbot) -> None:
    """Test the _show_manage_devices_dialog() method."""
    # Check that the dialog is created if it doesn't exist
    assert not hasattr(hw_sets, "_manage_devices_dialog")
    hw_sets._show_manage_devices_dialog()
    dialog = hw_sets._manage_devices_dialog
    assert not dialog.isHidden()

    # If it already exists, check it is shown
    dialog.hide()
    hw_sets._show_manage_devices_dialog()
    assert not dialog.isHidden()
    assert hw_sets._manage_devices_dialog is dialog
