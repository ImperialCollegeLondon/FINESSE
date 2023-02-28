"""Tests for the ScriptPathWidget."""
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from finesse.gui.measure_script.script_path_widget import ScriptPathWidget


class DummyWidget(ScriptPathWidget):
    """Override abstract member functions so we can create an instance."""

    def try_get_path_from_dialog(self) -> Optional[Path]:
        """Try to get the file name by raising a dialog."""
        return super().try_get_path_from_dialog()


@pytest.fixture()
def widget(qtbot) -> ScriptPathWidget:
    """Return a ScriptPathWidget for testing."""
    return DummyWidget()


def test_init(qtbot) -> None:
    """Check that the value of the QLineEdit is set correctly."""
    path = Path("/my/path")
    widget = DummyWidget(path)
    assert widget.line_edit.text() == str(path)

    widget = DummyWidget()
    assert widget.line_edit.text() == ""


def test_browse_button_connected(qtbot) -> None:
    """Check that the right signals are connected."""
    my_mock = MagicMock()
    with patch.object(DummyWidget, "setLayout"):
        with patch(
            "finesse.gui.measure_script.script_path_widget.QPushButton"
        ) as button_mock:
            button_mock.return_value = my_mock
            with patch("finesse.gui.measure_script.script_path_widget.QHBoxLayout"):
                widget = DummyWidget()
                my_mock.clicked.connect.assert_called_once_with(widget._browse_clicked)


@pytest.mark.parametrize("path", (None, Path("/my/path")))
def test_browse_button_clicked(path: Optional[Path], widget: ScriptPathWidget) -> None:
    """Check that the correct action is performed when the button is clicked."""
    with patch.object(widget, "try_get_path_from_dialog") as dialog_mock:
        with patch.object(widget, "set_path") as set_path_mock:
            dialog_mock.return_value = path

            widget._browse_clicked()
            if path:
                set_path_mock.assert_called_once_with(path)
            else:
                set_path_mock.assert_not_called()


def test_set_path(widget: ScriptPathWidget) -> None:
    """Test the set_path() method."""
    path = Path("/new/path")
    widget.set_path(path)
    assert widget.line_edit.text() == str(path)


@pytest.mark.parametrize(
    "widget_path,dialog_path",
    (
        (widget_path, dialog_path)
        for widget_path in (None, Path("/widget/path"))
        for dialog_path in (None, Path("/dialog/path"))
    ),
)
def test_try_get_path(
    widget_path: Optional[Path], dialog_path: Optional[Path], widget: ScriptPathWidget
) -> None:
    """Test the try_get_path() method.

    If the user has not already entered a value into the line edit, a dialog will be
    raised to allow them to choose the path.
    """
    if widget_path:
        widget.set_path(widget_path)
        assert widget.try_get_path() == widget_path
    else:
        with patch.object(widget, "try_get_path_from_dialog") as dialog_mock:
            dialog_mock.return_value = dialog_path
            assert widget.try_get_path() == dialog_path
