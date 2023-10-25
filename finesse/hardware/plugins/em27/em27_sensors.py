"""This module provides an interface to the EM27 monitor.

This is used to scrape the PSF27Sensor data table off the server.
"""
from decimal import Decimal
from functools import partial

from pubsub import pub
from PySide6.QtCore import Slot
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from finesse.config import EM27_URL
from finesse.em27_info import EM27Property
from finesse.hardware.pubsub_decorators import pubsub_broadcast


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


class EM27Error(Exception):
    """Indicates than an error occurred while parsing the webpage."""


@Slot()
@pubsub_broadcast("em27.error", "em27.data.response", "data")
def _on_reply_received(reply: QNetworkReply) -> list[EM27Property]:
    if reply.error() != QNetworkReply.NetworkError.NoError:
        raise EM27Error(f"Network error: {reply.errorString()}")

    content = reply.readAll().data().decode()
    return get_em27sensor_data(content)


class EM27Sensors:
    """An interface for monitoring EM27 properties."""

    def __init__(self, url: str = EM27_URL) -> None:
        """Create a new EM27 property monitor.

        Args:
            url: Web address of the automation units diagnostics page.
        """
        self._url: str = url
        self._timeout: float = 2.0
        self._manager = QNetworkAccessManager()

        pub.subscribe(self.send_data, "em27.data.request")

    def send_data(self) -> None:
        """Request the EM27 property data from the web server.

        The HTTP request is made on a background thread.
        """
        request = QNetworkRequest(self._url)
        request.setTransferTimeout(round(1000 * self._timeout))
        reply = self._manager.get(request)
        reply.finished.connect(partial(_on_reply_received, reply))
