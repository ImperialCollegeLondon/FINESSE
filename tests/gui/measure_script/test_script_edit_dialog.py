"""Tests for the ScriptEditDialog class and associated code."""
from collections.abc import Sequence
from contextlib import nullcontext
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, mock_open, patch

import pytest
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, QWidget
from pytestqt.qtbot import QtBot

from finesse.gui.measure_script.script import Measurement, Script
from finesse.gui.measure_script.script_edit_dialog import ScriptEditDialog


@pytest.fixture()
def dlg(qtbot: QtBot):
    """A test fixture providing a ScriptEditDialog."""
    parent = QWidget()
    yield ScriptEditDialog(parent)


_TEST_SCRIPT = Script(Path("/my/path"), 2, ({"angle": "nadir", "measurements": 3},))


@pytest.mark.parametrize(
    "script,count,sequence,script_path",
    (
        (None, 1, [], ""),  # no script supplied (i.e. create a new script)
        (
            _TEST_SCRIPT,
            _TEST_SCRIPT.repeats,
            _TEST_SCRIPT.sequence,
            str(_TEST_SCRIPT.path),
        ),
    ),
)
def test_init(
    qtbot: QtBot,
    script: Script | None,
    count: int,
    sequence: Sequence[Measurement],
    script_path: str,
) -> None:
    """Test ScriptEditDialog's constructor."""
    parent = QWidget()
    dlg = ScriptEditDialog(parent, script)
    assert dlg.count.value() == count
    assert dlg.sequence_widget.sequence == sequence
    assert dlg.script_path.line_edit.text() == script_path


_MEASUREMENTS = [Measurement(float(i), i) for i in range(1, 4)]


def _check_return(
    seq: list[Measurement], selected_path: bool, read_succeeds: bool
) -> Any:
    returns = not seq or (selected_path and read_succeeds)
    return seq, selected_path, read_succeeds, returns


@pytest.mark.parametrize(
    "seq,selected_path,read_succeeds,returns",
    [
        _check_return(_MEASUREMENTS[:n], selected_path, read_succeeds)
        for n in range(len(_MEASUREMENTS))
        for selected_path in (True, False)
        for read_succeeds in (True, False)
    ],
)
def test_try_save(
    seq: list[Measurement],
    selected_path: bool,
    read_succeeds: bool,
    returns: bool,
    dlg: ScriptEditDialog,
) -> None:
    """Test the _try_save() method."""
    with patch(
        "finesse.gui.measure_script.script_edit_dialog.show_error_message", MagicMock()
    ) as errmsg_mock:
        with patch("builtins.open", mock_open()) as open_mock:
            if not read_succeeds:
                open_mock.side_effect = Exception()

            with patch.object(dlg.script_path, "try_get_path") as path_mock:
                path_mock.return_value = (
                    Path("/my/path.yaml") if selected_path else None
                )

                dlg.sequence_widget.sequence = seq
                assert dlg._try_save() == returns

                if seq and selected_path and not read_succeeds:
                    errmsg_mock.assert_called_once()


@pytest.mark.parametrize("saved", (True, False))
def test_accept(saved: bool, qtbot: QtBot, dlg: ScriptEditDialog) -> None:
    """Check the Save button."""
    with patch.object(dlg, "_try_save") as try_save_mock:
        try_save_mock.return_value = saved

        # We only accept if _try_save() succeeds
        with qtbot.waitSignal(dlg.accepted) if saved else nullcontext():
            save_btn = dlg.buttonBox.button(QDialogButtonBox.StandardButton.Save)
            save_btn.click()


def test_reject(qtbot: QtBot, dlg: ScriptEditDialog) -> None:
    """Check the Cancel button."""
    with qtbot.waitSignal(dlg.rejected):
        cancel_btn = dlg.buttonBox.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_btn.click()


@pytest.mark.parametrize(
    "visible,nonempty_seq,btn_pressed,saved",
    (
        (visible, nonempty_seq, btn_pressed, saved)
        for visible in (True, False)
        for nonempty_seq in (True, False)
        for btn_pressed in (
            QMessageBox.StandardButton.Save,
            QMessageBox.StandardButton.Discard,
            QMessageBox.StandardButton.Cancel,
        )
        for saved in (True, False)
    ),
)
def test_close(
    visible: bool,
    nonempty_seq: bool,
    btn_pressed: int,
    saved: bool,
    qtbot: QtBot,
    dlg: ScriptEditDialog,
) -> None:
    """Test the effect of closing the dialog."""
    dlg.setModal(True)
    if visible:
        dlg.show()
        assert dlg.isVisible()

    if nonempty_seq:
        dlg.sequence_widget.sequence.append(Measurement(0.0, 1))

    with patch(
        "finesse.gui.measure_script.script_edit_dialog.QMessageBox"
    ) as msgbox_mock:
        # **HACK**: We just want to mock the exec method, but this is the only solution
        # I could find
        mock2 = MagicMock()
        msgbox_mock.return_value = mock2
        mock2.exec.return_value = int(btn_pressed)
        msgbox_mock.StandardButton = QMessageBox.StandardButton

        with patch.object(dlg, "setResult") as set_result_mock:
            with patch.object(dlg, "_try_save") as try_save_mock:
                try_save_mock.return_value = saved

                closed = dlg.close()

                if not visible or not nonempty_seq:
                    set_result_mock.assert_called_once_with(QDialog.DialogCode.Accepted)
                    return

                msgbox_mock.assert_called_once()
                if btn_pressed == QMessageBox.StandardButton.Discard:
                    set_result_mock.assert_called_once_with(QDialog.DialogCode.Rejected)
                    assert closed
                elif btn_pressed == QMessageBox.StandardButton.Save and saved:
                    set_result_mock.assert_called_once_with(QDialog.DialogCode.Accepted)
                    assert closed
                else:
                    set_result_mock.assert_not_called()
                    assert not closed
