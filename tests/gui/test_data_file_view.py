"""Tests for DataFileControl."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from finesse.gui.data_file_view import DataFileControl

FILE_PATH = Path("/path/to/file.csv")


@pytest.fixture
def data_file(qtbot) -> DataFileControl:
    """Provides a DataFileControl."""
    return DataFileControl()


def test_init(qtbot) -> None:
    """Test DataFileControl's constructor."""
    data_file = DataFileControl()
    assert data_file.record_btn.text() == "Start recording"
    assert data_file.save_path_widget.isEnabled()


def test_start_recording(
    data_file: DataFileControl, sendmsg_mock: MagicMock, qtbot
) -> None:
    """Test that recording starts correctly."""
    assert data_file.record_btn.text() == "Start recording"
    data_file.save_path_widget.set_path(FILE_PATH)
    data_file.record_btn.click()
    assert data_file.record_btn.text() == "Stop recording"
    sendmsg_mock.assert_called_once_with("data_file.open", path=FILE_PATH)


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
        sendmsg_mock.assert_not_called()


def test_stop_recording(
    data_file: DataFileControl, sendmsg_mock: MagicMock, qtbot
) -> None:
    """Test that recording stops correctly."""
    data_file.save_path_widget.set_path(FILE_PATH)
    data_file.record_btn.click()
    sendmsg_mock.reset_mock()

    data_file.record_btn.click()
    assert data_file.record_btn.text() == "Start recording"
    sendmsg_mock.assert_called_once_with("data_file.close")
