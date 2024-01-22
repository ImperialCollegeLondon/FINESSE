"""Test the DeviceTypeControl class."""
from collections.abc import Sequence
from unittest.mock import MagicMock, Mock, PropertyMock, call, patch

import pytest

from finesse.device_info import DeviceInstanceRef, DeviceParameter, DeviceTypeInfo
from finesse.gui.hardware_set.device_view import (
    DeviceParametersWidget,
    DeviceTypeControl,
)

DEVICE_TYPES = [
    DeviceTypeInfo("my_class1", "Device 1"),
    DeviceTypeInfo("my_class2", "Device 2"),
]


@pytest.fixture
def widget(subscribe_mock: MagicMock, qtbot) -> DeviceTypeControl:
    """Create a DeviceTypeControl fixture."""
    return DeviceTypeControl(
        "Device type", DeviceInstanceRef("base_type"), DEVICE_TYPES, None
    )


@pytest.mark.parametrize(
    "connected_device,previous_device,expected_device",
    (
        (connected, previous, connected if connected else default)
        for previous, default in (
            (None, DEVICE_TYPES[0]),
            (DEVICE_TYPES[1], DEVICE_TYPES[1]),
        )
        for connected in (None, DEVICE_TYPES[0])
    ),
)
@patch(
    "finesse.gui.hardware_set.device_view."
    "DeviceParametersWidget.load_saved_parameter_values"
)
@patch(
    "finesse.gui.hardware_set.device_view."
    "DeviceTypeControl._update_open_btn_enabled_state"
)
@patch("finesse.gui.hardware_set.device_view.settings")
def test_init(
    settings_mock: Mock,
    update_btn_mock: Mock,
    load_saved_mock: Mock,
    connected_device: DeviceTypeInfo | None,
    previous_device: DeviceTypeInfo | None,
    expected_device: DeviceTypeInfo,
    subscribe_mock: MagicMock,
    qtbot,
) -> None:
    """Test the constructor."""
    instance = DeviceInstanceRef("base_type")

    settings_mock.value.return_value = (
        previous_device.class_name if previous_device else None
    )
    widget = DeviceTypeControl(
        "Base type",
        instance,
        DEVICE_TYPES,
        connected_device_type=connected_device.class_name if connected_device else None,
    )
    assert widget._device_instance is instance
    items = [
        widget._device_combo.itemText(i) for i in range(widget._device_combo.count())
    ]
    assert items == [t.description for t in DEVICE_TYPES]
    assert [w.device_type for w in widget._device_widgets] == DEVICE_TYPES

    assert widget._device_combo.currentText() == expected_device.description

    if connected_device and connected_device.class_name == expected_device.class_name:
        assert widget._open_close_btn.text() == "Close"
    else:
        assert widget._open_close_btn.text() == "Open"

    # This should be called at least once. As it will also be called when the selected
    # device type changes, it may be called more than once.
    update_btn_mock.assert_called_once_with()

    subscribe_mock.assert_has_calls(
        [
            call(widget._on_device_opened, f"device.opening.{instance!s}"),
            call(widget._on_device_closed, f"device.closed.{instance!s}"),
        ]
    )

    assert len(widget.findChildren(DeviceParametersWidget)) == 1


def test_init_no_device_types(qtbot) -> None:
    """Test that the constructor raises an exception when no device types specified."""
    with pytest.raises(RuntimeError):
        DeviceTypeControl("Device type", DeviceInstanceRef("base_type"), [], None)


@pytest.mark.parametrize(
    "params,expected_enabled",
    (
        ({"param_not_poss": DeviceParameter("", ())}, False),
        (
            {"param_poss": DeviceParameter("", range(2))},
            True,
        ),
        (
            {
                "param_not_poss": DeviceParameter("", ()),
                "param_poss": DeviceParameter("", range(2)),
            },
            False,
        ),
        (
            {
                "param_poss1": DeviceParameter("", range(2)),
                "param_poss2": DeviceParameter("", range(2)),
            },
            True,
        ),
    ),
)
@patch(
    "finesse.gui.hardware_set.device_view.DeviceTypeControl.current_device_type_widget",
    new_callable=PropertyMock,
)
def test_update_open_btn_enabled_state(
    widget_mock: Mock,
    params: Sequence[DeviceParameter],
    expected_enabled: bool,
    widget: DeviceTypeControl,
    qtbot,
) -> None:
    """Test the _update_open_btn_enabled_state() method.

    The open/close button should be disabled if there are no possible values for at
    least one parameter and enabled otherwise.
    """
    widget_mock.device_type.parameters = params
    with patch.object(widget, "_open_close_btn") as btn_mock:
        widget._update_open_btn_enabled_state()
        btn_mock.setEnabled(expected_enabled)


def test_change_device_type(widget: DeviceTypeControl, qtbot) -> None:
    """Test that changing the selected device type causes the GUI to update."""
    with patch.object(widget, "_update_open_btn_enabled_state") as update_btn_mock:
        assert widget.layout().itemAt(1).widget() is widget._device_widgets[0]
        widget._device_combo.setCurrentIndex(1)
        assert widget.layout().itemAt(1).widget() is widget._device_widgets[1]
        assert widget._device_widgets[0].isHidden()
        assert not widget._device_widgets[1].isHidden()
        update_btn_mock.assert_called_once_with()


@pytest.mark.parametrize("enable", (True, False))
@patch(
    "finesse.gui.hardware_set.device_view.DeviceTypeControl.current_device_type_widget",
    new_callable=PropertyMock,
)
def test_set_combos_enabled(
    widget_mock: Mock, enable: bool, widget: DeviceTypeControl, qtbot
) -> None:
    """Test the _set_combos_enabled() method."""
    device_widget = MagicMock()
    widget_mock.return_value = device_widget
    with patch.object(widget, "_device_combo") as combo_mock:
        widget._set_combos_enabled(enable)
        combo_mock.setEnabled.assert_called_once_with(enable)
        device_widget.setEnabled.assert_called_once_with(enable)


def test_select_device(widget: DeviceTypeControl, qtbot) -> None:
    """Test the _select_device() method."""
    with patch.object(
        widget._device_widgets[1], "load_saved_parameter_values"
    ) as load_params_mock:
        assert widget._device_combo.currentIndex() == 0
        widget._select_device(DEVICE_TYPES[1].class_name)
        assert widget._device_combo.currentIndex() == 1
        load_params_mock.assert_called_once_with()


@patch("finesse.gui.hardware_set.device_view.logging.warn")
def test_select_device_unknown_device(
    warn_mock: Mock, widget: DeviceTypeControl, qtbot
) -> None:
    """Test the _select_device() method with an unknown device."""
    assert widget._device_combo.currentIndex() == 0
    widget._select_device("made_up_class")
    assert widget._device_combo.currentIndex() == 0
    warn_mock.assert_called_once()


@patch("finesse.gui.hardware_set.device_view.open_device")
def test_open_device(open_device_mock: Mock, widget: DeviceTypeControl, qtbot) -> None:
    """Test the _open_device() method."""
    widget._open_device()
    open_device_mock.assert_called_once_with(
        DEVICE_TYPES[0].class_name,
        widget._device_instance,
        widget._device_widgets[0].current_parameter_values,
    )


@patch("finesse.gui.hardware_set.device_view.show_error_message")
@patch(
    "finesse.gui.hardware_set.device_view"
    ".DeviceParametersWidget.current_parameter_values",
    new_callable=PropertyMock,
)
def test_open_device_bad_params(
    get_params_mock: Mock, error_message_mock: Mock, widget: DeviceTypeControl, qtbot
) -> None:
    """Test that a dialog is shown when parameter values are invalid."""
    get_params_mock.side_effect = ValueError
    widget._open_device()
    error_message_mock.assert_called_once()


@patch("finesse.gui.hardware_set.device_view.close_device")
def test_close_device(
    close_device_mock: Mock, widget: DeviceTypeControl, qtbot
) -> None:
    """Test the _close_device() method."""
    widget._close_device()
    close_device_mock.assert_called_once_with(widget._device_instance)


def test_on_device_opened(widget: DeviceTypeControl, qtbot) -> None:
    """Test the _on_device_opened() method."""
    with patch.object(widget, "_set_device_opened") as open_mock:
        widget._on_device_opened(DeviceInstanceRef("base_type"), "some_class", {})
        open_mock.assert_called_once_with("some_class")


def test_on_device_closed(widget: DeviceTypeControl, qtbot) -> None:
    """Test the _on_device_closed() method."""
    with patch.object(widget, "_set_device_closed") as close_mock:
        widget._on_device_closed(DeviceInstanceRef("base_type"))
        close_mock.assert_called_once_with()


def test_open_close_btn(widget: DeviceTypeControl, qtbot) -> None:
    """Test the open/close button works."""
    with patch.object(widget, "_open_device") as open_mock:
        with patch.object(widget, "_close_device") as close_mock:
            assert widget._open_close_btn.text() == "Open"
            widget._open_close_btn.click()
            open_mock.assert_called_once_with()
            close_mock.assert_not_called()

            open_mock.reset_mock()
            widget._open_close_btn.setText("Close")
            widget._open_close_btn.click()
            open_mock.assert_not_called()
            close_mock.assert_called_once_with()
