"""Tests for the SpectrometerBase class."""
from unittest.mock import call, patch

import pytest

from finesse.hardware.plugins.spectrometer.spectrometer_base import SpectrometerBase
from finesse.spectrometer_status import SpectrometerStatus


class _MockSpectrometer(SpectrometerBase, description="Mock spectrometer"):
    def connect(self) -> None:
        pass

    def start_measuring(self) -> None:
        pass

    def stop_measuring(self) -> None:
        pass

    def cancel_measuring(self) -> None:
        pass


def test_init() -> None:
    """Test the constructor."""
    with patch.object(_MockSpectrometer, "subscribe") as subscribe_mock:
        dev = _MockSpectrometer()
        commands = ("connect", "start_measuring", "stop_measuring", "cancel_measuring")
        subscribe_mock.assert_has_calls(
            [call(getattr(dev, command), command) for command in commands],
            any_order=True,
        )


@pytest.mark.parametrize("status", SpectrometerStatus)
def test_send_status_message(status: SpectrometerStatus) -> None:
    """Test the send_status_message() method."""
    with patch.object(_MockSpectrometer, "send_message") as sendmsg_mock:
        dev = _MockSpectrometer()
        dev.send_status_message(status)
        sendmsg_mock.assert_called_once_with(
            f"status.{status.name.lower()}", status=status
        )
