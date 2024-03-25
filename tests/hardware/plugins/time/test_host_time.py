"""Tests for the HostTime plugin."""

from unittest.mock import patch

from finesse.hardware.plugins.time.host_time import HostTime


@patch("finesse.hardware.plugins.time.host_time.time")
def test_get_time(time_mock) -> None:
    """Test the get_time() method."""
    time_mock.return_value = 1234.5678
    assert HostTime().get_time() == 1234.5678
    time_mock.assert_called_once()
