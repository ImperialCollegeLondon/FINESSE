"""This module provides an interface to the DECADES API.

This is used to query the DECADES server for aircraft sensor data.
"""
import json

from PySide6.QtCore import QTimer, Slot
from PySide6.QtNetwork import QNetworkReply

from finesse.config import (
    DECADES_HOST,
    DECADES_SENSORS_POLL_INTERVAL,
    DECADES_SENSORS_TOPIC,
    DECADES_SENSORS_URL,
)
from finesse.hardware.device import Device
from finesse.hardware.http_requester import HTTPRequester


def get_decades_sensor_data(content: list[dict]) -> list[dict]:
    """Parse and return sensor data from a DECADES server query.

    Args:
        content: The content of the HTTP response from the DECADES server

    Returns:
        None
    """
    # TODO: Parse sensor data.
    for sensor in content:
        print(sensor)

    return content


@Slot()
def _on_reply_received(reply: QNetworkReply) -> list[dict]:
    """Handle received HTTP reply.

    Args:
        reply: the response from the server
    """
    if reply.error() != QNetworkReply.NetworkError.NoError:
        raise DecadesError(f"Error: {reply.errorString()}")

    content = json.loads(reply.readAll().data().decode())
    return get_decades_sensor_data(content)


class DecadesError(Exception):
    """Indicates that an error occurred while querying the DECADES server."""


class DecadesSensorsBase(
    Device,
    name=DECADES_SENSORS_TOPIC,
    description="DECADES sensors",
):
    """An interface for monitoring generic DECADES sensor servers."""

    def __init__(self, url: str) -> None:
        """Create a new DECADES sensor monitor.

        Args:
            url: Address of the DECADES sensor data.
        """
        super().__init__()
        self._url: str = url
        self._requester = HTTPRequester()

        # Poll device once on open.
        # TODO: Run this synchronously so we can check that things work before the
        # device.opened message is sent
        self.send_data()

    def send_data(self) -> None:
        """Request the sensor data from the DECADES server.

        The HTTP request is made on a background thread.
        """
        self._requester.make_request(
            self._url,
            self.pubsub_broadcast(_on_reply_received, "data.response", "data"),
        )


class DecadesSensors(
    DecadesSensorsBase,
    description="DECADES sensors",
    parameters={
        "host": "The IP address or hostname of the DECADES server",
        "poll_interval": "How often to poll the device in seconds",
    },
):
    """A class for monitoring a DECADES sensor server."""

    def __init__(
        self,
        host: str = DECADES_HOST,
        poll_interval: float = DECADES_SENSORS_POLL_INTERVAL,
    ) -> None:
        """Create a new DecadesSensors.

        Args:
            host: The IP address or hostname of the DECADES server
            poll_interval: How often to poll the sensors (seconds)
        """
        super().__init__(DECADES_SENSORS_URL.format(host=host))
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self.send_data)
        self._poll_timer.start(int(poll_interval * 1000))

    def close(self) -> None:
        """Close the device."""
        self._poll_timer.stop()
