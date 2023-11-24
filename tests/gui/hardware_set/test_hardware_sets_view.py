"""Tests for the HardwareSetsControl class."""
from collections.abc import Sequence
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from unittest.mock import MagicMock, Mock, PropertyMock, call, patch

import pytest

from finesse.gui.hardware_set.hardware_set import HardwareSet, OpenDeviceArgs
from finesse.gui.hardware_set.hardware_sets_view import HardwareSetsControl


@pytest.fixture
@patch.object(HardwareSetsControl, "_update_control_state")
@patch.object(HardwareSetsControl, "_load_last_selected_hardware_set")
@patch("finesse.gui.hardware_set.hardware_sets_view.get_hardware_sets")
def hw_control(
    get_hw_sets_mock: Mock,
    update_mock: Mock,
    load_mock: Mock,
    hw_sets: Sequence[HardwareSet],
    sendmsg_mock: MagicMock,
    subscribe_mock: MagicMock,
    qtbot,
) -> HardwareSetsControl:
    """A fixture for the control."""
    get_hw_sets_mock.return_value = iter(hw_sets)
    return HardwareSetsControl()


@patch.object(HardwareSetsControl, "_load_hardware_set_list")
@patch.object(HardwareSetsControl, "_update_control_state")
@patch.object(HardwareSetsControl, "_load_last_selected_hardware_set")
def test_init(
    load_last_mock: Mock,
    update_mock: Mock,
    load_mock: Mock,
    subscribe_mock: MagicMock,
    qtbot,
) -> None:
    """Test the constructor."""
    hw_sets = HardwareSetsControl()
    load_mock.assert_called_once_with()
    load_last_mock.assert_called_once_with()
    update_mock.assert_called_once_with()

    subscribe_mock.assert_has_calls(
        (
            call(hw_sets._on_device_opened, "device.opening"),
            call(hw_sets._on_device_closed, "device.closed"),
            call(hw_sets._on_hardware_set_added, "hardware_set.added"),
            call(hw_sets._load_hardware_set_list, "hardware_set.removed"),
        ),
        any_order=True,
    )


@pytest.mark.parametrize(
    "selected_hw_set,expected_selection",
    ((None, "Test 1"), ("Test 1", "Test 1"), ("Test 2", "Test 2")),
)
@patch("finesse.gui.hardware_set.hardware_sets_view.settings")
def test_load_last_selected_hardware_set(
    settings_mock: Mock,
    selected_hw_set: str,
    expected_selection: str | None,
    hw_control: HardwareSetsControl,
    qtbot,
) -> None:
    """Test the _load_last_selected_hardware_set() method."""
    settings_mock.value.return_value = selected_hw_set
    hw_control._load_last_selected_hardware_set()
    settings_mock.value.assert_called_once_with("hardware_set/selected")
    assert hw_control._combo.currentText() == expected_selection


@patch("finesse.gui.hardware_set.hardware_sets_view.get_hardware_sets")
def test_load_hardware_set_list(
    get_hw_sets_mock: Mock, hw_control: HardwareSetsControl, qtbot
) -> None:
    """Test the _load_hardware_set_list() method."""
    get_hw_sets_mock.return_value = range(2)
    with patch.object(hw_control, "_add_hardware_set") as add_mock:
        hw_control._load_hardware_set_list()
        add_mock.assert_has_calls((call(0), call(1)))


@patch.object(HardwareSet, "load")
@patch("finesse.gui.hardware_set.hardware_sets_view.show_error_message")
@patch("finesse.gui.hardware_set.hardware_sets_view.QFileDialog.getOpenFileName")
def test_import_hardware_set_success(
    open_file_mock: Mock,
    error_message_mock: Mock,
    load_mock: Mock,
    hw_control: HardwareSetsControl,
    sendmsg_mock: MagicMock,
    qtbot,
) -> None:
    """Test the _import_hardware_set() method when a file is loaded successfully."""
    path = Path("dir/file.txt")
    hw_set = MagicMock()
    load_mock.return_value = hw_set
    open_file_mock.return_value = (str(path), None)
    hw_control._import_hardware_set()
    load_mock.assert_called_once_with(path)
    sendmsg_mock.assert_called_once_with("hardware_set.add", hw_set=hw_set)
    error_message_mock.assert_not_called()


@patch.object(HardwareSet, "load")
@patch("finesse.gui.hardware_set.hardware_sets_view.show_error_message")
@patch("finesse.gui.hardware_set.hardware_sets_view.QFileDialog.getOpenFileName")
def test_import_hardware_set_cancelled(
    open_file_mock: Mock,
    error_message_mock: Mock,
    load_mock: Mock,
    hw_control: HardwareSetsControl,
    sendmsg_mock: MagicMock,
    qtbot,
) -> None:
    """Test the _import_hardware_set() method when the dialog is closed."""
    open_file_mock.return_value = (None, None)
    hw_control._import_hardware_set()
    sendmsg_mock.assert_not_called()
    error_message_mock.assert_not_called()
    load_mock.assert_not_called()


@patch.object(HardwareSet, "load")
@patch("finesse.gui.hardware_set.hardware_sets_view.show_error_message")
@patch("finesse.gui.hardware_set.hardware_sets_view.QFileDialog.getOpenFileName")
def test_import_hardware_set_error(
    open_file_mock: Mock,
    error_message_mock: Mock,
    load_mock: Mock,
    hw_control: HardwareSetsControl,
    sendmsg_mock: MagicMock,
    qtbot,
) -> None:
    """Test the _import_hardware_set() method when a file fails to load."""
    path = Path("dir/file.txt")
    load_mock.side_effect = RuntimeError
    open_file_mock.return_value = (str(path), None)
    hw_control._import_hardware_set()
    load_mock.assert_called_once_with(path)
    sendmsg_mock.assert_not_called()
    error_message_mock.assert_called_once()


_HW_SET = HardwareSet(
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
)


@pytest.mark.parametrize(
    "existing_hw_sets,hw_set_name,expected_name,built_in",
    (
        ((), _HW_SET.name, _HW_SET.name, False),
        ((_HW_SET,), _HW_SET.name, f"{_HW_SET.name} (2)", False),
        ((_HW_SET, _HW_SET), _HW_SET.name, f"{_HW_SET.name} (3)", False),
        ((), _HW_SET.name, f"{_HW_SET.name} (built in)", True),
        ((_HW_SET,), _HW_SET.name, f"{_HW_SET.name} (built in) (2)", True),
        (
            (_HW_SET, _HW_SET),
            _HW_SET.name,
            f"{_HW_SET.name} (built in) (3)",
            True,
        ),
    ),
)
def test_add_hardware_set(
    existing_hw_sets: Sequence[HardwareSet],
    hw_set_name: str,
    expected_name: str,
    built_in: bool,
    hw_control: HardwareSetsControl,
    qtbot,
) -> None:
    """Test the _add_hardware_set() method."""
    hw_control._combo.clear()
    for hw_set in existing_hw_sets:
        hw_set = HardwareSet(hw_set.name, hw_set.devices, hw_set.file_path, built_in)
        hw_control._add_hardware_set(hw_set)

    with patch.object(hw_control._combo, "addItem") as add_mock:
        hw_set = HardwareSet(hw_set_name, frozenset(), Path(), built_in)
        hw_control._add_hardware_set(hw_set)
        add_mock.assert_called_once_with(expected_name, hw_set)


@patch.object(HardwareSetsControl, "_load_hardware_set_list")
def test_on_hardware_set_added(
    load_mock: Mock,
    hw_control: HardwareSetsControl,
    hw_sets: Sequence[HardwareSet],
    qtbot,
) -> None:
    """Test the _on_hardware_set_added() method."""
    with patch.object(hw_control, "_combo") as combo_mock:
        combo_mock.itemData = lambda idx: hw_sets[idx]
        combo_mock.count.return_value = len(hw_sets)
        hw_control._on_hardware_set_added(hw_sets[1])
        load_mock.assert_called_once_with()
        combo_mock.setCurrentIndex.assert_called_once_with(1)


def test_current_hardware_set(hw_control: HardwareSetsControl, qtbot) -> None:
    """Test the current_hardware_set property."""
    with patch.object(hw_control._combo, "currentData") as data_mock:
        hw_set = MagicMock()
        data_mock.return_value = hw_set
        assert hw_control.current_hardware_set is hw_set.devices

        # Should also work if no hardware set is selected
        data_mock.return_value = None
        assert hw_control.current_hardware_set == frozenset()


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
    hw_control: HardwareSetsControl,
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
            hw_control, "_connected_devices", _get_devices(connected_devices)
        ):
            with patch.object(
                hw_control._connect_btn, "setEnabled"
            ) as connect_enable_mock:
                with patch.object(
                    hw_control._disconnect_btn, "setEnabled"
                ) as disconnect_enable_mock:
                    hw_control._update_control_state()
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
    hw_control: HardwareSetsControl,
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
            hw_control, "_connected_devices", _get_devices(connected_devices)
        ):
            hw_control._connect_btn.click()

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
    close_mock: Mock, hw_control: HardwareSetsControl, qtbot
) -> None:
    """Test the disconnect button."""
    with patch.object(hw_control, "_update_control_state") as update_mock:
        with patch.object(hw_control, "_connected_devices", DEVICES):
            hw_control._disconnect_btn.setEnabled(True)
            hw_control._disconnect_btn.click()
            close_mock.assert_has_calls([call(device.instance) for device in DEVICES])
            update_mock.assert_called_once_with()


@patch("finesse.gui.hardware_set.hardware_sets_view.settings")
def test_on_device_opened(
    settings_mock: Mock, hw_control: HardwareSetsControl, qtbot
) -> None:
    """Test the _on_device_opened() method."""
    device = DEVICES[0]
    assert not hw_control._connected_devices
    with patch.object(hw_control, "_update_control_state") as update_mock:
        hw_control._on_device_opened(
            instance=device.instance, class_name=device.class_name, params=device.params
        )
        assert hw_control._connected_devices == {device}
        update_mock.assert_called_once_with()
        settings_mock.setValue.assert_has_calls(
            [
                call(f"device/type/{device.instance!s}", device.class_name),
                call(f"device/params/{device.class_name}", device.params),
            ]
        )


def test_on_device_closed(hw_control: HardwareSetsControl, qtbot) -> None:
    """Test the _on_device_closed() method."""
    device = DEVICES[0]
    assert not hw_control._connected_devices
    with patch.object(hw_control, "_update_control_state") as update_mock:
        hw_control._connected_devices.add(device)
        hw_control._on_device_closed(device.instance)
        assert not hw_control._connected_devices
        update_mock.assert_called_once_with()


def test_on_device_closed_not_found(hw_control: HardwareSetsControl, qtbot) -> None:
    """Test that _on_device_closed() does not raise an error if device is not found."""
    device = DEVICES[0]
    assert not hw_control._connected_devices
    with does_not_raise():
        hw_control._on_device_closed(device.instance)


def test_show_manage_devices_dialog(hw_control: HardwareSetsControl, qtbot) -> None:
    """Test the _show_manage_devices_dialog() method."""
    # Check that the dialog is created if it doesn't exist
    assert not hasattr(hw_control, "_manage_devices_dialog")
    hw_control._show_manage_devices_dialog()
    dialog = hw_control._manage_devices_dialog
    assert not dialog.isHidden()

    # If it already exists, check it is shown
    dialog.hide()
    hw_control._show_manage_devices_dialog()
    assert not dialog.isHidden()
    assert hw_control._manage_devices_dialog is dialog


def test_remove_hw_set_btn(
    hw_control: HardwareSetsControl, sendmsg_mock: Mock, qtbot
) -> None:
    """Test that _remove_hw_set_btn works."""
    with patch.object(hw_control._combo, "currentData") as data_mock:
        hw_set = MagicMock()
        data_mock.return_value = hw_set
        hw_control._remove_hw_set_btn.click()
        sendmsg_mock.assert_called_once_with("hardware_set.remove", hw_set=hw_set)
