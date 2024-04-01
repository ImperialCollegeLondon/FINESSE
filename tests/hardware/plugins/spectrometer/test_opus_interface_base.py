"""Test the OPUSInterfaceBase class."""

from unittest.mock import MagicMock

import pytest

from finesse.hardware.plugins.spectrometer.opus_interface_base import OPUSInterfaceBase


class _MockOPUS(OPUSInterfaceBase, description="Mock OPUS device"):
    def __init__(self):
        super().__init__()
        self._request_mock = MagicMock()

    def request_command(self, command: str):
        self._request_mock(command)

    def assert_command_requested(self, command: str):
        self._request_mock.assert_called_once_with(command)


@pytest.fixture
def opus() -> _MockOPUS:
    """Provides an OPUS device with request_command() mocked."""
    return _MockOPUS()


def test_connect(opus: _MockOPUS) -> None:
    """Test the connect() method."""
    opus.connect()
    opus.assert_command_requested("connect")


def test_start_measuring(opus: _MockOPUS) -> None:
    """Test the start_measuring() method."""
    opus.start_measuring()
    opus.assert_command_requested("start")


def test_stop_measuring(opus: _MockOPUS) -> None:
    """Test the stop_measuring() method."""
    opus.stop_measuring()
    opus.assert_command_requested("cancel")
