"""This module provides an interface to the EM27 monitor.

This is used to scrape the PSF27 sensor data table off the server.
"""
from dataclasses import dataclass
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from pubsub import pub

# from ..config import EM27_IP
EM27_IP = "10.10.0.1"


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

    def __str__(self) -> str:
        """For printing a property's name, value and unit in a readable format.

        Returns:
            str: The name, value and unit of a property.
        """
        return f"{self.name} = {self.value:.6f} {self.unit}"

    def val_str(self) -> str:
        """For printing a property's value and unit in required format.

        Returns:
            str: The value and unit of a property in the format consistent with
                 the previous FINESSE GUI.
        """
        return f"{self.value:.6f} {self.unit}"


class EM27Scraper:
    """An interface for monitoring EM27 properties."""

    def __init__(self, url: str = f"http://{EM27_IP}/diag_autom.htm") -> None:
        """Create a new EM27 property monitor.

        Args:
            url: Web address of the automation units diagnostics page.
        """
        self._is_open = False
        self._is_read = False
        self._url = url
        self._data_table: list[EM27Property] = []

    def open(self, timeout: int = 2) -> int:
        """Connect to the webpage.

        Args:
            timeout: Number of seconds to wait for response.

        Returns:
            error: 0 = successful open, 1 = unsuccessful open
        """
        if self._is_open:
            return 0

        error = 1
        try:
            self._page = urlopen(self._url, timeout=timeout)
            self._is_open = True
            error = 0
        except HTTPError as exception:
            print(exception)
        except URLError as exception:
            print(exception)
        except TimeoutError:
            print("Request timed out")

        return error

    def close(self) -> int:
        """Disconnect from the webpage.

        Returns:
            error: 0 = successful close, 1 = unsuccessful close
        """
        if not self._is_open:
            return 0

        error = 1
        try:
            self._page.close()
            self._is_open = False
            error = 0
        except AttributeError:
            print("Page has not been opened")
        return error

    def read(self) -> int:
        """Read the webpage and store in EM27 object.

        Returns:
            error: 0 = successful read, 1 = unsuccessful read
        """
        error = 1
        if self._is_open:
            try:
                self._html = self._page.read()
                self._is_read = True
                error = 0
            except AttributeError:
                print("Page has not been opened")
        else:
            print("Page is closed")
        return error

    def get_psf27sensor_data(self) -> int:
        """Search for the PSF27Sensor table and store the data.

        Returns:
            error: 0 = successful search, 1 = unsuccessful search
        """
        error = 1
        if self._is_read:
            try:
                html_ascii = self._html.decode("ascii")
            except AttributeError:
                print("Page has not been read")
            else:
                table_header = (
                    "<TR><TH>No</TH><TH>Name</TH><TH>Description</TH>"
                    + "<TH>Status</TH><TH>Value</TH><TH>Meas. Unit</TH></TR>\n"
                )
                table_start = html_ascii.find(table_header)
                try:
                    assert table_start != -1
                    error = 0
                except AssertionError:
                    print("PSF27Sensor table not located")
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


class DummyEM27Scraper(EM27Scraper):
    """An interface for EM27 monitor testing."""

    def __init__(self) -> None:
        """Create a new monitor for a dummy EM27."""
        super().__init__("file:///home/dc2917/Downloads/diag_autom.htm")


if __name__ == "__main__":
    dev = DummyEM27Scraper()
    error = dev.open()
    print(error)
    error = dev.read()
    print(error)
    error = dev.get_psf27sensor_data()
    print(error)
    if not error:
        for prop in dev._data_table:
            print(prop)
    error = dev.close()
    print(error)
