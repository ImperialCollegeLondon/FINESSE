"""Tests for ScriptControl."""
from itertools import product
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, Mock, patch

import pytest
from PySide6.QtWidgets import QPushButton, QWidget
from pytestqt.qtbot import QtBot

from finesse.config import DEFAULT_SCRIPT_PATH
from finesse.em27_info import EM27Status
from finesse.gui.measure_script.script_run_dialog import ScriptRunDialog
from finesse.gui.measure_script.script_view import ScriptControl


@pytest.fixture
@patch("finesse.gui.measure_script.script_view.settings")
def script_control(settings_mock: Mock, qtbot: QtBot) -> ScriptControl:
    """Provides a ScriptControl."""
    # NB: This will need to be changed if we load more than one setting
    settings_mock.value.return_value = "/my/path.yaml"
    return ScriptControl()


def get_button(widget: QWidget, text: str) -> QPushButton:
    """Get the button with the specified text label."""
    buttons = cast(list[QPushButton], widget.findChildren(QPushButton))
    return next(btn for btn in buttons if btn.text() == text)


def click_button(widget: QWidget, text: str) -> None:
    """Click the button with the specified text label."""
    get_button(widget, text).click()


@patch("finesse.gui.measure_script.script_view.settings")
def test_init(settings_mock: Mock, subscribe_mock: Mock, qtbot: QtBot) -> None:
    """Test ScriptControl's constructor."""
    settings_mock.value.return_value = "/my/path.yaml"
    script_control = ScriptControl()

    # Check we are subscribed to the relevant pubsub messages
    subscribe_mock.assert_any_call(
        script_control._show_run_dialog, "measure_script.begin"
    )
    subscribe_mock.assert_any_call(
        script_control._hide_run_dialog, "measure_script.end"
    )
    subscribe_mock.assert_any_call(script_control._on_opus_message, "opus.response")
    assert not script_control._opus_connected


@patch("finesse.gui.measure_script.script_view.settings")
@pytest.mark.parametrize("prev_path", (Path("/my/path.yaml"), ""))
def test_init_path_setting(settings_mock: Mock, prev_path: Path, qtbot: QtBot) -> None:
    """Check that the constructor correctly loads previous path from settings."""
    settings_mock.value.return_value = str(prev_path)
    script_control = ScriptControl()

    # NB: This will need to be changed if we load more than one setting
    settings_mock.value.assert_called_once_with("script/run_path", "")

    # Check that the initial path is correct
    assert script_control.script_path.line_edit.text() == str(prev_path)


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
        assert script_control.edit_dialog is dialog
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
        assert script_control.edit_dialog is dialog
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

        btn = get_button(script_control, "Run script")
        btn.setEnabled(True)  # Will be disabled unless devices are connected
        btn.click()

        # Check that settings were updated
        settings_mock.setValue.assert_any_call("script/run_path", str(script_path))

        # Check that the script was started
        script.run.assert_called_once_with(script_control)


@patch("finesse.gui.measure_script.script_view.ScriptRunDialog")
def test_show_run_dialog(
    run_dialog_mock: Mock,
    script_control: ScriptControl,
    qtbot: QtBot,
) -> None:
    """Test the _show_run_dialog() method."""
    dialog = MagicMock()
    run_dialog_mock.return_value = dialog

    with patch.object(script_control, "window") as window_mock:
        window = MagicMock()
        window_mock.return_value = window

        runner = MagicMock()
        script_control._show_run_dialog(runner)

        # Check that the dialog was created and shown
        run_dialog_mock.assert_called_once_with(window, runner)
        assert script_control.run_dialog is dialog
        dialog.show.assert_called_once_with()


def test_hide_run_dialog(
    script_control: ScriptControl,
    run_dialog: ScriptRunDialog,
    sendmsg_mock: MagicMock,
    qtbot: QtBot,
) -> None:
    """Test the _hide_run_dialog() method."""
    dialog = MagicMock()
    script_control.run_dialog = dialog
    script_control._hide_run_dialog()

    dialog.hide.assert_called_once_with()  # Check window is hidden
    assert not hasattr(script_control, "run_dialog")  # Check attribute is deleted


def test_hide_run_dialog_no_abort(
    script_control: ScriptControl,
    run_dialog: ScriptRunDialog,
    sendmsg_mock: MagicMock,
    qtbot: QtBot,
) -> None:
    """Test the _hide_run_dialog() method doesn't abort the measure script.

    This method should only be run when the measure script completes successfully.
    """
    script_control.run_dialog = run_dialog
    script_control._hide_run_dialog()

    # Check that measure_script.abort message isn't sent
    sendmsg_mock.assert_not_called()


@pytest.mark.parametrize(
    "status,already_connected",
    product((EM27Status(i) for i in range(2, 6)), (True, False)),
)
def test_on_opus_message_connect(
    status: EM27Status,
    already_connected: bool,
    script_control: ScriptControl,
    qtbot: QtBot,
) -> None:
    """Test the _on_opus_message() method when connecting."""
    script_control._opus_connected = already_connected

    with patch.object(script_control, "_enable_counter") as counter_mock:
        script_control._on_opus_message(status, "")
        if already_connected:
            counter_mock.increment.assert_not_called()
        else:
            counter_mock.increment.assert_called_once_with()

        assert script_control._opus_connected


@pytest.mark.parametrize(
    "status,already_connected",
    product((EM27Status.CONNECTING, EM27Status.UNDEFINED), (True, False)),
)
def test_on_opus_message_disconnect(
    status: EM27Status,
    already_connected: bool,
    script_control: ScriptControl,
    qtbot: QtBot,
) -> None:
    """Test the _on_opus_message() method when disconnecting."""
    script_control._opus_connected = already_connected

    with patch.object(script_control, "_enable_counter") as counter_mock:
        script_control._on_opus_message(status, "")
        if not already_connected:
            counter_mock.decrement.assert_not_called()
        else:
            counter_mock.decrement.assert_called_once_with()

        assert not script_control._opus_connected
