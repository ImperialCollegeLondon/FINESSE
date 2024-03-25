"""Tests for the HostTime plugin."""
from unittest.mock import patch

from finesse.hardware.plugins.time.host_time import HostTime


@patch("finesse.hardware.plugins.time.host_time.datetime")
def test_get_time(datetime_mock) -> None:
    """Test the get_time() method."""
    datetime_mock.now.return_value = 1234.5678
    assert HostTime().get_time() == 1234.5678
    datetime_mock.now.assert_called_once()
