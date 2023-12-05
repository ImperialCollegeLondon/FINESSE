"""Test the OPUSInterfaceBase class."""
from unittest.mock import MagicMock, Mock, patch

import pytest

from finesse.config import SPECTROMETER_TOPIC
from finesse.hardware.plugins.spectrometer.opus_interface_base import OPUSInterfaceBase
from finesse.spectrometer_status import SpectrometerStatus


class _MyOPUSClass(OPUSInterfaceBase, description="My OPUS class"):
    def request_command(self, command: str) -> None:
        pass


@patch("finesse.hardware.plugins.spectrometer.opus_interface_base.Device.subscribe")
def test_init(subscribe_mock: Mock) -> None:
    """Test the constructor."""
    opus = _MyOPUSClass()
    subscribe_mock.assert_called_once_with(opus.request_command, "request")


@pytest.mark.parametrize("status", SpectrometerStatus)
def test_send_status_message(
    status: SpectrometerStatus, sendmsg_mock: MagicMock
) -> None:
    """Test the send_status_message() method."""
    opus = _MyOPUSClass()
    opus.send_status_message(status)
    sendmsg_mock.assert_called_once_with(
        f"device.{SPECTROMETER_TOPIC}.status.{status.name.lower()}", status=status
    )
