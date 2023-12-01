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
@patch.object(HardwareSetsControl, "_update_control_state")
@patch.object(HardwareSetsControl, "_load_last_selected_hardware_set")
@patch("finesse.gui.hardware_set.hardware_sets_view.get_hardware_sets")
def hw_sets(
    get_hw_sets_mock: Mock,
    update_mock: Mock,
    load_mock: Mock,
    sendmsg_mock: MagicMock,
    subscribe_mock: MagicMock,
    qtbot,
) -> HardwareSetsControl:
    """A fixture for the control."""
    get_hw_sets_mock.return_value = iter(HW_SETS)
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
        [
            call(hw_sets._on_device_opened, "device.opening"),
            call(hw_sets._on_device_closed, "device.closed"),
            call(hw_sets._on_hardware_set_added, "hardware_set.added"),
        ]
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
    hw_sets: HardwareSetsControl,
    qtbot,
) -> None:
    """Test the _load_last_selected_hardware_set() method."""
    settings_mock.value.return_value = selected_hw_set
    hw_sets._load_last_selected_hardware_set()
    settings_mock.value.assert_called_once_with("hardware_set/selected")
    assert hw_sets._hardware_sets_combo.currentText() == expected_selection


@patch("finesse.gui.hardware_set.hardware_sets_view.get_hardware_sets")
def test_load_hardware_set_list(
    get_hw_sets_mock: Mock, hw_sets: HardwareSetsControl, qtbot
) -> None:
    """Test the _load_hardware_set_list() method."""
    get_hw_sets_mock.return_value = range(2)
    with patch.object(hw_sets, "_add_hardware_set") as add_mock:
        hw_sets._load_hardware_set_list()
        add_mock.assert_has_calls((call(0), call(1)))


@patch.object(HardwareSet, "load")
@patch("finesse.gui.hardware_set.hardware_sets_view.show_error_message")
@patch("finesse.gui.hardware_set.hardware_sets_view.QFileDialog.getOpenFileName")
def test_import_hardware_set_success(
    open_file_mock: Mock,
    error_message_mock: Mock,
    load_mock: Mock,
    hw_sets: HardwareSetsControl,
    sendmsg_mock: MagicMock,
    qtbot,
) -> None:
    """Test the _import_hardware_set() method when a file is loaded successfully."""
    path = Path("dir/file.txt")
    hw_set = MagicMock()
    load_mock.return_value = hw_set
    open_file_mock.return_value = (str(path), None)
    hw_sets._import_hardware_set()
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
    hw_sets: HardwareSetsControl,
    sendmsg_mock: MagicMock,
    qtbot,
) -> None:
    """Test the _import_hardware_set() method when the dialog is closed."""
    open_file_mock.return_value = (None, None)
    hw_sets._import_hardware_set()
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
    hw_sets: HardwareSetsControl,
    sendmsg_mock: MagicMock,
    qtbot,
) -> None:
    """Test the _import_hardware_set() method when a file fails to load."""
    path = Path("dir/file.txt")
    load_mock.side_effect = RuntimeError
    open_file_mock.return_value = (str(path), None)
    hw_sets._import_hardware_set()
    load_mock.assert_called_once_with(path)
    sendmsg_mock.assert_not_called()
    error_message_mock.assert_called_once()


@pytest.mark.parametrize(
    "existing_hw_sets,hw_set_name,expected_name,built_in",
    (
        ((), HW_SETS[0].name, HW_SETS[0].name, False),
        ((HW_SETS[0],), HW_SETS[0].name, f"{HW_SETS[0].name} (2)", False),
        ((HW_SETS[0], HW_SETS[0]), HW_SETS[0].name, f"{HW_SETS[0].name} (3)", False),
        ((), HW_SETS[0].name, f"{HW_SETS[0].name} (built in)", True),
        ((HW_SETS[0],), HW_SETS[0].name, f"{HW_SETS[0].name} (built in) (2)", True),
        (
            (HW_SETS[0], HW_SETS[0]),
            HW_SETS[0].name,
            f"{HW_SETS[0].name} (built in) (3)",
            True,
        ),
    ),
)
def test_add_hardware_set(
    existing_hw_sets: Sequence[HardwareSet],
    hw_set_name: str,
    expected_name: str,
    built_in: bool,
    hw_sets: HardwareSetsControl,
    qtbot,
) -> None:
    """Test the _add_hardware_set() method."""
    # Patch this function, because it'll break if the combo box is empty
    with patch.object(hw_sets, "_update_control_state"):
        hw_sets._hardware_sets_combo.clear()
        for hw_set in existing_hw_sets:
            hw_set = HardwareSet(
                hw_set.name, hw_set.devices, hw_set.file_path, built_in
            )
            hw_sets._add_hardware_set(hw_set)

        with patch.object(hw_sets._hardware_sets_combo, "addItem") as add_mock:
            hw_set = HardwareSet(hw_set_name, frozenset(), Path(), built_in)
            hw_sets._add_hardware_set(hw_set)
            add_mock.assert_called_once_with(expected_name, hw_set)


@patch.object(HardwareSetsControl, "_load_hardware_set_list")
def test_on_hardware_set_added(
    load_mock: Mock, hw_sets: HardwareSetsControl, qtbot
) -> None:
    """Test the _on_hardware_set_added() method."""
    with patch.object(hw_sets, "_hardware_sets_combo") as combo_mock:
        combo_mock.itemData = lambda idx: HW_SETS[idx]
        combo_mock.count.return_value = len(HW_SETS)
        hw_sets._on_hardware_set_added(HW_SETS[1])
        combo_mock.clear.assert_called_once_with()
        load_mock.assert_called_once_with()
        combo_mock.setCurrentIndex.assert_called_once_with(1)


def test_current_hardware_set(hw_sets: HardwareSetsControl, qtbot) -> None:
    """Test the current_hardware_set property."""
    with patch.object(hw_sets._hardware_sets_combo, "currentData") as data_mock:
        hw_set = MagicMock()
        data_mock.return_value = hw_set
        assert hw_sets.current_hardware_set is hw_set.devices

        # Should also work if no hardware set is selected
        data_mock.return_value = None
        assert hw_sets.current_hardware_set == frozenset()


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
                call(f"device/type/{device.instance!s}", device.class_name),
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
