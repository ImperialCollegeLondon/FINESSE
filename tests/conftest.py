"""Configuration for pytest."""
from unittest.mock import MagicMock

import pytest
from pubsub import pub


@pytest.fixture
def sendmsg_mock(monkeypatch) -> MagicMock:
    """Fixture for pub.sendMessage."""
    mock = MagicMock()
    monkeypatch.setattr(pub, "sendMessage", mock)
    return mock
