"""Tests for the SensorsBase class."""

from typing import cast
from unittest.mock import MagicMock, Mock, patch

import pytest

from finesse.hardware.plugins.sensors.sensors_base import SensorsBase


@pytest.fixture
@patch("finesse.hardware.plugins.sensors.sensors_base.QTimer")
def device(timer_mock: Mock) -> SensorsBase:
    """Provides a mock sensors device."""
    return _MockSensorsDevice()


class _MockSensorsDevice(SensorsBase, description="Mock sensors device"):
    def __init__(self, poll_interval: float = float("nan"), start_polling=True):
        self.request_readings_mock = MagicMock()
        super().__init__(poll_interval, start_polling)

    def request_readings(self) -> None:
        self.request_readings_mock()


@pytest.mark.parametrize("start_polling", (False, True))
@patch("finesse.hardware.plugins.sensors.sensors_base.QTimer")
def test_init(timer_mock: Mock, start_polling: bool) -> None:
    """Test for the constructor."""
    with patch.object(_MockSensorsDevice, "start_polling") as start_mock:
        device = _MockSensorsDevice(1.0, start_polling)
        assert device._poll_interval == 1.0
        timer = cast(Mock, device._poll_timer)
        timer.timeout.connect.assert_called_once_with(device.request_readings)

        if start_polling:
            start_mock.assert_called_once_with()
        else:
            start_mock.assert_not_called()


@patch("finesse.hardware.plugins.sensors.sensors_base.QTimer")
def test_start_polling_oneshot(timer_mock: Mock) -> None:
    """Test the start_polling() method when polling is only done once."""
    device = _MockSensorsDevice(start_polling=False)

    device.start_polling()
    timer = cast(Mock, device._poll_timer)
    timer.start.assert_not_called()


@patch("finesse.hardware.plugins.sensors.sensors_base.QTimer")
def test_start_polling_repeated(timer_mock: Mock) -> None:
    """Test the start_polling() method when polling is only done repeatedly."""
    device = _MockSensorsDevice(1.0, start_polling=False)

    device.start_polling()
    timer = cast(Mock, device._poll_timer)
    timer.start.assert_called_once_with(1000)


@patch("finesse.hardware.plugins.sensors.sensors_base.QTimer")
def test_init_no_timer(timer_mock: Mock) -> None:
    """Test for the constructor when the user has disabled polling."""
    device = _MockSensorsDevice()
    timer = cast(Mock, device._poll_timer)
    timer.start.assert_not_called()


def test_send_readings_message(device: SensorsBase) -> None:
    """Test the send_readings_message() method."""
    with patch.object(device, "send_message") as sendmsg_mock:
        readings = MagicMock()
        device.send_readings_message(readings)
        sendmsg_mock.assert_called_once_with("data", readings=readings)


def test_close(device: SensorsBase) -> None:
    """Test the close method stops the timer."""
    device.close()
    timer = cast(Mock, device._poll_timer)
    timer.stop.assert_called_once_with()
