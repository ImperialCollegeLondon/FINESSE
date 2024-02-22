"""This module provides an interface for querying time from an NTP server."""
from ntplib import NTPClient

from finesse.config import TIME_NTP_HOST
from finesse.hardware.plugins.time.time_base import TimeBase


class NTPTimeError(Exception):
    """Indicates that an error occurred while querying the NTP time server."""


class NTPTime(
    TimeBase,
    description="NTP time",
    parameters={
        "ntp_host": "The NTP server to query",
    },
):
    """A time source that queries an NTP server."""

    def __init__(self, ntp_host: str = TIME_NTP_HOST) -> None:
        """Create a new NTPTime.

        Args:
            ntp_host: The IP address or hostname of the NTP server
        """
        super().__init__()
        self._client = NTPClient()
        self._ntp_host = ntp_host
        self._ntp_version = 3
        self._ntp_port = "ntp"
        self._ntp_timeout = 5

    def close(self) -> None:
        """Close the connection to the device."""

    def get_time(self) -> float:
        """Get the current time."""
        try:
            response = self._client.request(
                self._ntp_host,
                version=self._ntp_version,
                port=self._ntp_port,
                timeout=self._ntp_timeout,
            )
        except Exception as e:
            raise NTPTimeError(f"Error querying NTP server: {e}")

        return response.dest_time + response.offset
