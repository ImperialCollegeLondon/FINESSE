"""Provides common fixtures for measure script tests."""
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from finesse.gui.measure_script.script import Script, ScriptRunner


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
