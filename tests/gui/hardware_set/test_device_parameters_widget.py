"""Tests for the DeviceParametersWidget class."""
from collections.abc import Mapping
from unittest.mock import Mock, patch

import pytest

from finesse.device_info import DeviceParameter, DeviceTypeInfo
from finesse.gui.hardware_set.device_view import DeviceParametersWidget


@pytest.fixture
def widget(qtbot) -> DeviceParametersWidget:
    """A fixture providing a DeviceParametersWidget."""
    return DeviceParametersWidget(
        DeviceTypeInfo("my_class", "My Device", {"my_param": DeviceParameter(range(2))})
    )


@pytest.mark.parametrize(
    "params",
    (
        # no params
        {},
        # one param
        {"my_param": DeviceParameter(("value1", "value2"))},
        # two params
        {
            "my_param": DeviceParameter(("value1", "value2")),
            "param2": DeviceParameter(range(3), 1),
        },
    ),
)
def test_init(params: Mapping[str, DeviceParameter], qtbot) -> None:
    """Test the constructor."""
    device_type = DeviceTypeInfo("my_class", "My Device", params)

    with patch.object(
        DeviceParametersWidget, "load_saved_parameter_values"
    ) as load_params_mock:
        widget = DeviceParametersWidget(device_type)
        assert widget.device_type is device_type
        assert widget._combos.keys() == params.keys()
        load_params_mock.assert_called_once_with()

        for name, param in params.items():
            combo = widget._combos[name]
            items = [combo.itemText(i) for i in range(combo.count())]
            assert items == list(map(str, param.possible_values))
            assert (
                combo.currentData() == param.default_value
                if param.default_value
                else param.possible_values[0]
            )


def test_set_parameter_value(widget: DeviceParametersWidget) -> None:
    """Test the set_parameter_value() method."""
    combo = widget._combos["my_param"]
    assert combo.currentText() == "0"

    widget.set_parameter_value("my_param", 1)
    assert combo.currentText() == "1"

    widget.set_parameter_value("my_param", 5)  # invalid
    assert combo.currentText() == "1"


@patch("finesse.gui.hardware_set.device_view.settings")
def test_load_saved_parameter_values(
    settings_mock: Mock, widget: DeviceParametersWidget, qtbot
) -> None:
    """Test the load_saved_parameter_values() method."""
    settings_mock.value.return_value = {"my_param": 1}
    with patch.object(widget, "set_parameter_value") as set_param_mock:
        widget.load_saved_parameter_values()
        set_param_mock.assert_called_once_with("my_param", 1)


@patch("finesse.gui.hardware_set.device_view.settings")
def test_load_saved_parameter_values_none_saved(
    settings_mock: Mock, widget: DeviceParametersWidget, qtbot
) -> None:
    """Test the load_saved_parameter_values() method if there are no values saved."""
    settings_mock.value.return_value = None
    with patch.object(widget, "set_parameter_value") as set_param_mock:
        widget.load_saved_parameter_values()
        set_param_mock.assert_not_called()


@patch("finesse.gui.hardware_set.device_view.settings")
@patch("finesse.gui.hardware_set.device_view.logging.warn")
def test_load_saved_parameter_values_error(
    warn_mock: Mock, settings_mock: Mock, widget: DeviceParametersWidget, qtbot
) -> None:
    """Test the load_saved_parameter_values() method ignores errors."""
    settings_mock.value.return_value = {"my_param": 1}
    with patch.object(widget, "set_parameter_value") as set_param_mock:
        set_param_mock.side_effect = KeyError
        widget.load_saved_parameter_values()
        set_param_mock.assert_called_once_with("my_param", 1)
        warn_mock.assert_called_once()


def test_current_parameter_values(widget: DeviceParametersWidget, qtbot) -> None:
    """Test the current_parameter_values property."""
    assert widget.current_parameter_values == {"my_param": 0}
