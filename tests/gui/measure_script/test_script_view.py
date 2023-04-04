"""Tests for ScriptControl."""
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, Mock, patch

import pytest
from PySide6.QtWidgets import QPushButton, QWidget
from pytestqt.qtbot import QtBot

from finesse.config import DEFAULT_SCRIPT_PATH
from finesse.gui.measure_script.script_view import ScriptControl


@pytest.fixture
@patch("finesse.gui.measure_script.script_view.settings")
def script_control(settings_mock: Mock, qtbot: QtBot) -> ScriptControl:
    """Provides a ScriptControl."""
    # NB: This will need to be changed if we load more than one setting
    settings_mock.value.return_value = "/my/path.yaml"
    return ScriptControl()


def click_button(widget: QWidget, text: str) -> None:
    """Click the button with the specified text label."""
    buttons = cast(list[QPushButton], widget.findChildren(QPushButton))
    btn = next(btn for btn in buttons if btn.text() == text)
    btn.click()


@patch("finesse.gui.measure_script.script_view.settings")
@pytest.mark.parametrize("prev_path", ("/my/path.yaml", ""))
def test_init(settings_mock: Mock, prev_path: str, qtbot: QtBot) -> None:
    """Check that the constructor correctly loads previous path from settings."""
    settings_mock.value.return_value = prev_path
    script_control = ScriptControl()

    # NB: This will need to be changed if we load more than one setting
    settings_mock.value.assert_called_once_with("script/run_path", "")

    # Check that the initial path is correct
    assert script_control.script_path.line_edit.text() == prev_path


@patch("finesse.gui.measure_script.script_view.ScriptEditDialog")
def test_create_button(
    edit_dialog_mock: Mock, script_control: ScriptControl, qtbot: QtBot
) -> None:
    """Test that the create button works."""
    dialog = MagicMock()
    edit_dialog_mock.return_value = dialog
    with patch.object(script_control, "window") as window_mock:
        window = MagicMock()
        window_mock.return_value = window

        click_button(script_control, "Create new script")

        # Check that dialog was created and shown
        edit_dialog_mock.assert_called_once_with(window)
        assert script_control.dialog is dialog
        dialog.show.assert_called_once_with()


@patch("finesse.gui.measure_script.script_view.Script")
@patch("finesse.gui.measure_script.script_view.QFileDialog")
@patch("finesse.gui.measure_script.script_view.ScriptEditDialog")
def test_edit_button_file_dialog_closed(
    edit_dialog_mock: Mock,
    file_dialog_mock: Mock,
    script_mock: Mock,
    script_control: ScriptControl,
    qtbot: QtBot,
) -> None:
    """Test that the edit button doesn't create a new dialog if file dialog closed."""
    file_dialog_mock.getOpenFileName.return_value = ("", "*.yaml")
    click_button(script_control, "Edit script")
    edit_dialog_mock.assert_not_called()


@patch("finesse.gui.measure_script.script_view.Script")
@patch("finesse.gui.measure_script.script_view.QFileDialog")
@patch("finesse.gui.measure_script.script_view.ScriptEditDialog")
def test_edit_button_bad_script(
    edit_dialog_mock: Mock,
    file_dialog_mock: Mock,
    script_mock: Mock,
    script_control: ScriptControl,
    qtbot: QtBot,
) -> None:
    """Test that the edit button behaves correctly when script fails to load."""
    file_dialog_mock.getOpenFileName.return_value = ("/my/path.yaml", "*.yaml")
    script_mock.try_load.return_value = None  # Indicates error

    click_button(script_control, "Edit script")
    edit_dialog_mock.assert_not_called()


@patch("finesse.gui.measure_script.script_view.Script")
@patch("finesse.gui.measure_script.script_view.QFileDialog")
@patch("finesse.gui.measure_script.script_view.ScriptEditDialog")
def test_edit_button_success(
    edit_dialog_mock: Mock,
    file_dialog_mock: Mock,
    script_mock: Mock,
    script_control: ScriptControl,
    qtbot: QtBot,
) -> None:
    """Test that the edit button creates a new dialog when no error occurs."""
    dialog = MagicMock()
    edit_dialog_mock.return_value = dialog
    file_dialog_mock.getOpenFileName.return_value = ("/my/path.yaml", "*.yaml")
    script = MagicMock()
    script_mock.try_load.return_value = script

    with patch.object(script_control, "window") as window_mock:
        window = MagicMock()
        window_mock.return_value = window
        click_button(script_control, "Edit script")

        # Check that a file dialog is opened with the correct parameters
        file_dialog_mock.getOpenFileName.assert_called_once_with(
            script_control,
            caption="Choose script file to edit",
            dir=str(DEFAULT_SCRIPT_PATH),
            filter="*.yaml",
        )

        # Check that a script is loaded from the correct path
        script_mock.try_load.assert_called_once_with(
            script_control, Path("/my/path.yaml")
        )

        # Check that dialog is created and shown
        edit_dialog_mock.assert_called_once_with(window, script)
        assert script_control.dialog is dialog
        dialog.show.assert_called_once_with()


@patch("finesse.gui.measure_script.script_view.settings")
@patch("finesse.gui.measure_script.script_view.Script")
def test_run_button_no_file_path(
    script_mock: Mock, settings_mock: Mock, script_control: ScriptControl, qtbot: QtBot
) -> None:
    """Test that the run button does nothing if no path selected."""
    with patch.object(script_control.script_path, "try_get_path") as try_get_path_mock:
        try_get_path_mock.return_value = None
        click_button(script_control, "Run script")

        # Check that function returns without loading script
        script_mock.try_load.assert_not_called()

        # Check that settings weren't updated
        settings_mock.setValue.assert_not_called()


@patch("finesse.gui.measure_script.script_view.settings")
@patch("finesse.gui.measure_script.script_view.Script")
def test_run_button_bad_script(
    script_mock: Mock, settings_mock: Mock, script_control: ScriptControl, qtbot: QtBot
) -> None:
    """Test that the run button does nothing if script fails to load."""
    script_mock.try_load.return_value = None
    click_button(script_control, "Run script")

    # Check that settings weren't updated
    settings_mock.setValue.assert_not_called()


@patch("finesse.gui.measure_script.script_view.settings")
@patch("finesse.gui.measure_script.script_view.Script")
def test_run_button_success(
    script_mock: Mock, settings_mock: Mock, script_control: ScriptControl, qtbot: QtBot
) -> None:
    """Test that the run button works if no error occurs."""
    with patch.object(script_control.script_path, "try_get_path") as try_get_path_mock:
        script_path = Path("/my/path.yaml")
        try_get_path_mock.return_value = script_path
        script = MagicMock()
        script_mock.try_load.return_value = script

        click_button(script_control, "Run script")

        # Check that settings were updated
        settings_mock.setValue.assert_any_call("script/run_path", str(script_path))

        # Check that the script was started
        script.run.assert_called_once_with(script_control)
