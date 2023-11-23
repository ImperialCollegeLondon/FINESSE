"""This module provides an interface to the EM27 monitor.

This is used to scrape the PSF27Sensor data table off the server.
"""
from decimal import Decimal

from PySide6.QtCore import QTimer, Slot
from PySide6.QtNetwork import QNetworkReply

from finesse.config import (
    EM27_HOST,
    EM27_SENSORS_POLL_INTERVAL,
    EM27_SENSORS_TOPIC,
    EM27_SENSORS_URL,
)
from finesse.em27_info import EM27Property
from finesse.hardware.device import Device
from finesse.hardware.http_requester import HTTPRequester


def get_em27sensor_data(content: str) -> list[EM27Property]:
    """Search for the PSF27Sensor table and store the data.

    Args:
        content: HTML content in which to search for PSF27Sensor table

    Returns:
        data_table: a list of sensor properties and their values
    """
    table_header = (
        "<TR><TH>No</TH><TH>Name</TH><TH>Description</TH>"
        + "<TH>Status</TH><TH>Value</TH><TH>Meas. Unit</TH></TR>"
    )
    table_start = content.find(table_header)
    if table_start == -1:
        raise EM27Error("PSF27Sensor table not found")

    table_end = table_start + content[table_start:].find("</TABLE>")
    table = content[table_start:table_end].splitlines()
    data_table = []
    for row in range(1, len(table)):
        data_table.append(
            EM27Property(
                table[row].split("<TD>")[2].rstrip("</TD>"),
                Decimal(table[row].split("<TD>")[5].strip("</TD>")),
                table[row].split("<TD>")[6].rstrip("</TD></TR"),
            )
        )

    return data_table


@Slot()
def _on_reply_received(reply: QNetworkReply) -> list[EM27Property]:
    """Handle received HTTP reply.

    Args:
        reply: the response from the server
    """
    if reply.error() != QNetworkReply.NetworkError.NoError:
        raise EM27Error(f"Network error: {reply.errorString()}")

    content = reply.readAll().data().decode()
    return get_em27sensor_data(content)


class EM27Error(Exception):
    """Indicates than an error occurred while parsing the webpage."""


class EM27SensorsBase(
    Device,
    is_base_type=True,
    name=EM27_SENSORS_TOPIC,
    description="EM27 sensors",
):
    """An interface for monitoring EM27 properties."""

    def __init__(self, url: str) -> None:
        """Create a new EM27 property monitor.

        Args:
            url: Web address of the automation units diagnostics page.
        """
        super().__init__()
        self._url: str = url
        self._requester = HTTPRequester()

        # Poll device once on open.
        # TODO: Run this synchronously so we can check that things work before the
        # device.opened message is sent
        self.send_data()

    def send_data(self) -> None:
        """Request the EM27 property data from the web server.

        The HTTP request is made on a background thread.
        """
        self._requester.make_request(
            self._url,
            self.pubsub_broadcast(_on_reply_received, "data.response", "data"),
        )


class EM27Sensors(
    EM27SensorsBase,
    description="EM27 sensors",
    parameters={
        "host": "The IP address or hostname of the EM27 device",
        "poll_interval": "How often to poll the device in seconds",
    },
):
    """An interface for EM27 sensors on the real device."""

    def __init__(
        self, host: str = EM27_HOST, poll_interval: float = EM27_SENSORS_POLL_INTERVAL
    ) -> None:
        """Create a new EM27Sensors.

        Args:
            host: The IP address or hostname of the EM27 device
            poll_interval: How often to poll the sensors (seconds)
        """
        super().__init__(EM27_SENSORS_URL.format(host=host))
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self.send_data)
        self._poll_timer.start(int(poll_interval * 1000))

    def close(self) -> None:
        """Close the device."""
        self._poll_timer.stop()
