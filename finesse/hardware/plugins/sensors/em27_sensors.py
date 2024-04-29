"""This module provides an interface to the EM27 monitor.

This is used to scrape the PSF27Sensor data table off the server.
"""

from decimal import Decimal

from PySide6.QtCore import Slot
from PySide6.QtNetwork import QNetworkReply

from finesse.config import EM27_HOST, EM27_SENSORS_POLL_INTERVAL, EM27_SENSORS_URL
from finesse.hardware.device import DeviceClassType
from finesse.hardware.http_requester import HTTPRequester
from finesse.hardware.plugins.sensors.sensors_base import SensorsBase
from finesse.sensor_reading import SensorReading


def get_em27_sensor_data(content: str) -> list[SensorReading]:
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
            SensorReading(
                table[row].split("<TD>")[2].rstrip("</TD>"),
                Decimal(table[row].split("<TD>")[5].strip("</TD>")),
                table[row].split("<TD>")[6].rstrip("</TD></TR"),
            )
        )

    return data_table


class EM27Error(Exception):
    """Indicates than an error occurred while parsing the webpage."""


class EM27SensorsBase(
    SensorsBase,
    class_type=DeviceClassType.IGNORE,
    description="EM27 sensors",
):
    """An interface for monitoring EM27 properties."""

    def __init__(self, url: str, poll_interval: float = float("nan")) -> None:
        """Create a new EM27 property monitor.

        Args:
            url: Web address of the automation units diagnostics page.
            poll_interval: How often to poll the device (seconds)
        """
        self._url: str = url
        self._requester = HTTPRequester()

        super().__init__(poll_interval)

    def request_readings(self) -> None:
        """Request the EM27 property data from the web server.

        The HTTP request is made on a background thread.
        """
        self._requester.make_request(
            self._url,
            self.pubsub_errors(self._on_reply_received),
        )

    @Slot()
    def _on_reply_received(self, reply: QNetworkReply) -> None:
        """Handle received HTTP reply.

        Args:
            reply: the response from the server
        """
        if reply.error() != QNetworkReply.NetworkError.NoError:
            raise EM27Error(f"Network error: {reply.errorString()}")

        content = reply.readAll().data().decode()
        readings = get_em27_sensor_data(content)
        self.send_readings_message(readings)


class EM27Sensors(
    EM27SensorsBase,
    description="EM27 sensors",
    parameters={"host": "The IP address or hostname of the EM27 device"},
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
        super().__init__(EM27_SENSORS_URL.format(host=host), poll_interval)
