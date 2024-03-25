"""Tests for the NTPTime plugin."""
from unittest.mock import patch

import pytest

from finesse.hardware.plugins.time.ntp_time import NTPTime, NTPTimeError


def test_init() -> None:
    """Test the NTPTime constructor."""
    ntp_time = NTPTime("pool.ntp.org")
    assert ntp_time._ntp_host == "pool.ntp.org"
    assert ntp_time._ntp_version == 3
    assert ntp_time._ntp_port == "ntp"
    assert ntp_time._ntp_timeout == 5


@patch("ntplib.NTPClient.request")
def test_get_time(request_mock) -> None:
    """Test the get_time() method arguments."""
    NTPTime("pool.ntp.org").get_time()
    request_mock.assert_called_once_with(
        "pool.ntp.org", version=3, port="ntp", timeout=5
    )


@patch("ntplib.NTPClient.request")
def test_get_time_return_value(request_mock) -> None:
    """Test the get_time() method return value."""
    ntp_time = NTPTime()
    request_mock.return_value.dest_time = 1234.5678
    request_mock.return_value.offset = 0.1234
    assert ntp_time.get_time().timestamp() == 1234.6912


@patch("ntplib.NTPClient.request", side_effect=Exception())
def test_get_time_exception(request_mock) -> None:
    """Test the get_time() method raises an exception on error."""
    ntp_time = NTPTime()
    with pytest.raises(NTPTimeError):
        ntp_time.get_time()
