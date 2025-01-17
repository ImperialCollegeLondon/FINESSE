"""Tests for the RecordingWidget class."""

from unittest.mock import Mock, call

import pytest
from pytestqt.qtbot import QtBot

from frog.gui.data_file_view import RecordingWidget


@pytest.fixture
def widget(qtbot: QtBot):
    """A fixture providing a RecordingWidget."""
    yield RecordingWidget()


def test_init(subscribe_mock: Mock, qtbot: QtBot) -> None:
    """Test RecordingWidget's constructor."""
    widget = RecordingWidget()
    assert widget._label.text() == "NOT RECORDING"
    assert widget._btn.text() == "Start recording"
    assert not widget._is_recording

    subscribe_mock.assert_has_calls(
        (
            call(widget._led.flash, "data_file.writing"),
            call(widget._on_file_open, "data_file.opened"),
            call(widget._on_file_close, "data_file.close"),
        ),
        any_order=True,
    )


def test_on_file_open(widget: RecordingWidget) -> None:
    """Test the _on_file_open() method."""
    widget._on_file_open()
    assert widget._is_recording
    assert widget._btn.text() == "Stop recording"
    assert (
        widget._label.text() == '<font color="red"><b>RECORDING IN PROGRESS</b></font>'
    )


def test_on_file_close(widget: RecordingWidget) -> None:
    """Test the _on_file_close() method."""
    # First, simulate opening the file
    widget._on_file_open()

    # Now check that everything resets correctly
    widget._on_file_close()
    assert not widget._is_recording
    assert widget._btn.text() == "Start recording"
    assert widget._label.text() == "NOT RECORDING"


def test_button(widget: RecordingWidget, qtbot: QtBot) -> None:
    """Test that recording is started and stopped correctly."""
    with qtbot.waitSignal(widget.start_recording):
        widget._btn.click()


def test_button_stop(widget: RecordingWidget, qtbot: QtBot) -> None:
    """Test that recording is stopped correctly."""
    widget._is_recording = True
    with qtbot.waitSignal(widget.stop_recording):
        widget._btn.click()
