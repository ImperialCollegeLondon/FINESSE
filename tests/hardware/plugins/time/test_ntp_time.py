"""Tests for the NTPTime plugin."""

from unittest.mock import patch

from finesse.hardware.plugins.time.ntp_time import NTPTime


@patch("ntplib.NTPClient.request")
def test_init(request_mock) -> None:
    """Test the NTPTime constructor."""
    ntp_time = NTPTime(
        ntp_host="test.org",
        ntp_version=2,
        ntp_port="test_port",
        ntp_timeout=123.0,
        ntp_poll_interval=456.0,
    )

    assert ntp_time._ntp_host == "test.org"
    assert ntp_time._ntp_version == 2
    assert ntp_time._ntp_port == "test_port"
    assert ntp_time._ntp_timeout == 123.0

    # Interval is in milliseconds, not seconds.
    assert ntp_time._poll_timer.interval() == 456000

    request_mock.assert_called_once_with(
        "test.org", version=2, port="test_port", timeout=123.0
    )


@patch("ntplib.NTPClient.request")
def test_poll_time_offset(request_mock) -> None:
    """Test the poll_time_offset method."""
    request_mock.return_value.offset = 1234.5678
    ntp_time = NTPTime(
        ntp_host="test.org",
        ntp_version=3,
        ntp_port="test_port",
        ntp_timeout=10.0,
    )

    request_mock.assert_called_once_with(
        "test.org", version=3, port="test_port", timeout=10.0
    )

    assert ntp_time._response.offset == 1234.5678


@patch("finesse.hardware.plugins.time.ntp_time.NTPTimeError")
@patch("finesse.hardware.plugins.time.ntp_time.NTPTime.send_error_message")
@patch("ntplib.NTPClient.request")
def test_poll_time_offset_error(request_mock, send_error_mock, error_mock) -> None:
    """Test the poll_time_offset method sends error messages for exceptions."""
    request_mock.side_effect = Exception()
    NTPTime()

    # poll_time_offset() is called once in the constructor.
    send_error_mock.assert_called_once_with(error_mock())


@patch("ntplib.NTPClient.request")
def test_get_time_offset(request_mock) -> None:
    """Test the get_time_offset method."""
    request_mock.return_value.offset = 1234.5678
    ntp_time = NTPTime()

    assert ntp_time.get_time_offset() == 1234.5678


@patch("PySide6.QtCore.QTimer.stop")
def test_close(stop_mock) -> None:
    """Test the close method."""
    ntp_time = NTPTime()
    ntp_time.close()

    stop_mock.assert_called_once()
