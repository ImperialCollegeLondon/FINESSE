"""Tests for the FTSW500InterfaceBase class."""

from unittest.mock import patch

import pytest

from frog.hardware.plugins.spectrometer.ftsw500_interface_base import (
    FTSW500InterfaceBase,
)


class _MockFTSW500Interface(FTSW500InterfaceBase, description="Mock FTSW500 interface"):
    """Dummy class for testing."""

    def request_command(self):
        """No-op."""


@pytest.mark.parametrize(
    "method,command",
    (
        ("connect", "clickConnectButton"),
        ("start_measuring", "clickStartAcquisitionButton"),
        ("stop_measuring", "clickStopAcquisitionButton"),
    ),
)
def test_methods(method: str, command: str) -> None:
    """Test FTSWInterfaceBase's non-virtual methods."""
    ftsw = _MockFTSW500Interface()
    with patch.object(ftsw, "request_command") as request_mock:
        # Invoke the specified method and check that the correct command was sent
        getattr(ftsw, method)()
        request_mock.assert_called_once_with(command)
