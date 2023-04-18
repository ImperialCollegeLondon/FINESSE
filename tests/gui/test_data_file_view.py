"""Tests for DataFileControl."""
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from finesse.gui.data_file_view import DataFileControl

FILE_PATH = Path("/path/to/file.csv")


@pytest.fixture
def data_file(qtbot) -> DataFileControl:
    """Provides a DataFileControl."""
    return DataFileControl()


def test_init(subscribe_mock: Mock, qtbot) -> None:
    """Test DataFileControl's constructor."""
    data_file = DataFileControl()
    assert data_file.record_btn.text() == "Start recording"
    assert data_file.save_path_widget.isEnabled()

    subscribe_mock.assert_any_call(data_file._on_file_open, "data_file.open")
    subscribe_mock.assert_any_call(data_file._on_file_close, "data_file.close")
    subscribe_mock.assert_any_call(data_file._show_error_message, "data_file.error")


# TODO: file open,close


def test_start_recording(
    data_file: DataFileControl, sendmsg_mock: MagicMock, qtbot
) -> None:
    """Test that recording starts correctly."""
    assert data_file.record_btn.text() == "Start recording"
    data_file.save_path_widget.set_path(FILE_PATH)
    data_file.record_btn.click()
    sendmsg_mock.assert_called_once_with("data_file.open", path=FILE_PATH)


def test_on_file_open(data_file: DataFileControl) -> None:
    """Test the _on_file_open() method."""
    data_file._on_file_open(FILE_PATH)
    assert data_file.record_btn.text() == "Stop recording"
    assert not data_file.save_path_widget.isEnabled()


def test_on_file_close(data_file: DataFileControl) -> None:
    """Test the _on_file_close() method."""
    # Simulate file open to start with
    data_file._on_file_open(FILE_PATH)

    # Simulate closing it again
    data_file._on_file_close()

    assert data_file.record_btn.text() == "Start recording"
    assert data_file.save_path_widget.isEnabled()


def test_start_recording_path_dialog_cancelled(
    data_file: DataFileControl, sendmsg_mock: MagicMock, qtbot
) -> None:
    """Check that recording isn't started if the user closes the file dialog."""
    assert data_file.save_path_widget.line_edit.text() == ""
    with patch.object(data_file.save_path_widget, "try_get_path") as path_mock:
        path_mock.return_value = None
        data_file.record_btn.click()
        path_mock.assert_called_once()
        assert data_file.record_btn.text() == "Start recording"
        assert data_file.save_path_widget.isEnabled()
        sendmsg_mock.assert_not_called()


def test_stop_recording(
    data_file: DataFileControl, sendmsg_mock: MagicMock, qtbot
) -> None:
    """Test that recording stops correctly."""
    # Simulate file open to start with
    data_file._on_file_open(FILE_PATH)

    data_file.record_btn.click()
    sendmsg_mock.assert_called_once_with("data_file.close")


@patch("finesse.gui.data_file_view.QMessageBox")
def test_show_error_message(msgbox_mock: Mock, data_file: DataFileControl) -> None:
    """Test the _show_error_message() method."""
    msgbox_mock.return_value = msgbox = MagicMock()
    error = Exception()
    data_file._show_error_message(error)
    msgbox_mock.assert_called_once_with(
        msgbox_mock.Icon.Critical,
        "Error writing to file",
        f"An error occurred while writing the data file: {str(error)}",
        msgbox_mock.StandardButton.Ok,
        data_file,
    )
    msgbox.exec.assert_called_once_with()
