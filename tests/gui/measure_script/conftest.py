"""Provides common fixtures for measure script tests."""
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QWidget
from pytestqt.qtbot import QtBot

from finesse.gui.measure_script.script import Script, ScriptRunner
from finesse.gui.measure_script.script_run_dialog import ScriptRunDialog


@pytest.fixture
def runner():
    """Fixture for a ScriptRunner in its initial state."""
    script = Script(Path(), 1, ({"angle": 0.0, "measurements": 3},))
    runner = ScriptRunner(script)
    runner._check_status_timer = MagicMock()
    return runner


@pytest.fixture
def runner_measuring(
    runner: ScriptRunner, subscribe_mock: MagicMock, sendmsg_mock: MagicMock
) -> ScriptRunner:
    """Fixture for a ScriptRunner in a measuring state."""
    runner.start_moving()
    runner.start_measuring()
    sendmsg_mock.reset_mock()
    return runner


@pytest.fixture
def run_dialog(
    runner: ScriptRunner, subscribe_mock: MagicMock, qtbot: QtBot
) -> Generator[ScriptRunDialog, None, None]:
    """Provides a ScriptRunDialog."""
    widget = QWidget()
    yield ScriptRunDialog(widget, runner)
