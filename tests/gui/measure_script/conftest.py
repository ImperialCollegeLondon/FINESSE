"""Provides common fixtures for measure script tests."""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytestqt.qtbot import QtBot

from finesse.gui.measure_script.script import Script, ScriptRunner
from finesse.gui.measure_script.script_run_dialog import ScriptRunDialog


@pytest.fixture
def runner(subscribe_mock: MagicMock, sendmsg_mock: MagicMock) -> ScriptRunner:
    """Fixture for a ScriptRunner in its initial state."""
    script = Script(Path(), 1, ({"angle": 0.0, "measurements": 3},))
    runner = ScriptRunner(script)
    subscribe_mock.reset_mock()
    sendmsg_mock.reset_mock()
    return runner


@pytest.fixture
def runner_measuring(
    runner: ScriptRunner,
    subscribe_mock: MagicMock,
    unsubscribe_mock: MagicMock,
    sendmsg_mock: MagicMock,
) -> ScriptRunner:
    """Fixture for a ScriptRunner in a measuring state."""
    runner.start_moving()
    runner.finish_moving()
    runner.start_measuring()
    subscribe_mock.reset_mock()
    unsubscribe_mock.reset_mock()
    sendmsg_mock.reset_mock()
    return runner


@pytest.fixture
def run_dialog(
    runner: ScriptRunner, subscribe_mock: MagicMock, qtbot: QtBot
) -> Generator[ScriptRunDialog, None, None]:
    """Provides a ScriptRunDialog."""
    yield ScriptRunDialog(runner)
