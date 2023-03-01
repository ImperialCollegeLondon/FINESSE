"""This module provides an interface to the EM27 monitor.

This is used to scrape the PSF27 sensor data table off the server.
"""
from dataclasses import dataclass
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from pubsub import pub


@dataclass
class EM27Property:
    """Class for representing EM27 monitored properties.

    Args:
        name: name of the physical quantity
        value: value of the physical quantity
        unit: unit in which the value is presented
    """

    name: str
    value: Decimal
    unit: str


class EM27:
    """An interface for EM27 monitoring."""

    def __init__(self, url: str = "http://10.10.0.1/diag_autom.htm") -> None:
        """Create a new EM27 monitor.

        Args:
            url: Web address of the automation units diagnostics page.
        """
        self._url = url
        self._html = b""
        self._data_table: list[EM27Property] = []

    def open(self, timeout: int = 2) -> int:
        """Connect to the webpage.

        Args:
            timeout: Number of seconds to wait for response.

        Returns:
            error: 0 = successful request, 1 = error
        """
        error = 1
        try:
            self._page = urlopen(self._url, timeout=timeout)
            error = 0
        except HTTPError as exception:
            print(exception.status, exception.reason)
        except URLError as exception:
            print(exception.reason)
        except TimeoutError:
            print("Request timed out")

        return error

    def close(self) -> None:
        """Disconnect from the webpage."""
        self._page.close()

    def read(self) -> int:
        """Read the webpage and store in EM27 object.

        Returns:
            error: 0 = successful read, 1 = error
        """
        error = 0
        try:
            self._html = self._page.read()
        except ValueError as exception:
            print(exception)
            print("Open page first")
            error = 1
        return error

    def get_psf27sensor_data(self) -> int:
        """Search for the PSF27Sensor table and store the data.

        Returns:
            error: 0 = successful request, 1 = error
        """
        error = 0
        html_ascii = self._html.decode("ascii")
        table_header = (
            "<TR><TH>No</TH><TH>Name</TH><TH>Description</TH>"
            + "<TH>Status</TH><TH>Value</TH><TH>Meas. Unit</TH></TR>\n"
        )
        table_start = html_ascii.find(table_header)
        if table_start == -1:
            error = 1
            print("Error: table not located")
            print(html_ascii)
        else:
            table_end = table_start + html_ascii[table_start:].find("</TABLE>")
            table = html_ascii[table_start:table_end].splitlines()
            for row in range(1, len(table) - 1):
                self._data_table.append(
                    EM27Property(
                        table[row].split("<TD>")[2].rstrip("</TD>"),
                        Decimal(table[row].split("<TD>")[5].strip("</TD>")),
                        table[row].split("<TD>")[6].rstrip("</TD></TR"),
                    )
                )
            pub.sendMessage("psf27_data", data=table)
        return error


class DummyEM27(EM27):
    """An interface for EM27 monitor testing."""

    def __init__(self) -> None:
        """Create a new monitor for a dummy EM27."""
        super().__init__("file:///home/dc2917/Downloads/diag_autom.htm")


if __name__ == "__main__":
    dev = DummyEM27()
    error = dev.open()
    print(error)
    error = dev.read()
    print(error)
    error = dev.get_psf27sensor_data()
    print(error)
    print(dev._data_table)
    dev.close()

    # tests:
    # 1) open correct webpage, check response
    # 1a)
    # 1b)
    # 2) attempt to open incorrect webpage
