"""Configuration for pytest."""

import os
from unittest.mock import MagicMock

import pytest
from pubsub import pub


@pytest.fixture
def serial_mock(monkeypatch) -> MagicMock:
    """Fixture for Serial's constructor."""
    from frog.hardware.serial_device import SerialDevice

    mock = MagicMock()

    def new_init(self, *args, **kwargs):
        self.serial = mock

    monkeypatch.setattr(SerialDevice, "__init__", new_init)
    return mock


@pytest.fixture
def subscribe_mock(monkeypatch) -> MagicMock:
    """Fixture for pub.subscribe."""
    mock = MagicMock()
    monkeypatch.setattr(pub, "subscribe", mock)
    return mock


@pytest.fixture
def unsubscribe_mock(monkeypatch) -> MagicMock:
    """Fixture for pub.subscribe."""
    mock = MagicMock()
    monkeypatch.setattr(pub, "unsubscribe", mock)
    return mock


@pytest.fixture
def sendmsg_mock(monkeypatch) -> MagicMock:
    """Fixture for pub.sendMessage."""
    mock = MagicMock()
    monkeypatch.setattr(pub, "sendMessage", mock)
    return mock


# Don't actually raise windows etc.
os.environ["QT_QPA_PLATFORM"] = "offscreen"
