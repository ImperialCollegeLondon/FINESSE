"""Tests for the NTPTime plugin."""

from unittest.mock import patch

import pytest

from frog.hardware.plugins.time.ntp_time import NTPTime, NTPTimeError


@patch("ntplib.NTPClient.request")
def test_init(request_mock) -> None:
    """Test the NTPTime constructor."""
    ntp_time = NTPTime(
        ntp_host="test.org",
        ntp_version=3,
        ntp_port=111,
        ntp_timeout=1.0,
        ntp_poll_interval=1.0,
    )

    assert ntp_time._ntp_host == "test.org"
    assert ntp_time._ntp_version == 3
    assert ntp_time._ntp_port == 111
    assert ntp_time._ntp_timeout == 1.0

    # Interval is in milliseconds, not seconds.
    assert ntp_time._poll_timer.interval() == 1000

    request_mock.assert_called_once_with("test.org", version=3, port=111, timeout=1.0)


@patch("ntplib.NTPClient.request")
def test_poll_time_offset(request_mock) -> None:
    """Test the poll_time_offset method."""
    request_mock.return_value.offset = 123.456
    ntp_time = NTPTime(
        ntp_host="test.org",
        ntp_version=3,
        ntp_port=111,
        ntp_timeout=1.0,
    )

    request_mock.assert_called_once_with("test.org", version=3, port=111, timeout=1.0)

    assert ntp_time._response.offset == 123.456


@patch("ntplib.NTPClient.request")
def test_poll_time_offset_error(request_mock) -> None:
    """Test the poll_time_offset method sends error messages for exceptions."""
    request_mock.side_effect = Exception()

    # poll_time_offset() is called once in the constructor.
    with pytest.raises(NTPTimeError):
        NTPTime()


@patch("ntplib.NTPClient.request")
def test_get_time_offset(request_mock) -> None:
    """Test the get_time_offset method."""
    request_mock.return_value.offset = 123.456
    ntp_time = NTPTime()

    assert ntp_time.get_time_offset() == 123.456


@patch("PySide6.QtCore.QTimer.stop")
@patch("ntplib.NTPClient.request")
def test_close(request_mock, stop_mock) -> None:
    """Test the close method."""
    ntp_time = NTPTime()
    ntp_time.close()

    stop_mock.assert_called_once()
