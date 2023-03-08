"""This module provides an interface to the EM27 monitor.

This is used to scrape the PSF27 sensor data table off the server.
"""
import logging
import traceback
from dataclasses import dataclass
from decimal import Decimal
from importlib import resources
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from pubsub import pub

from ..config import EM27_URL


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
        """Print a property's name, value and unit in a readable format.

        Returns:
            str: The name, value and unit of a property.
        """
        return f"{self.name} = {self.value:.6f} {self.unit}"

    def val_str(self) -> str:
        """Print a property's value and unit in required format.

        Returns:
            str: The value and unit of a property in the format consistent with
                 the previous FINESSE GUI.
        """
        return f"{self.value:.6f} {self.unit}"


class PSF27Error(Exception):
    """Indicates than an error occurred while parsing the webpage."""


class EM27Scraper:
    """An interface for monitoring EM27 properties."""

    def __init__(self, url: str = f"{EM27_URL}") -> None:
        """Create a new EM27 property monitor.

        Args:
            url: Web address of the automation units diagnostics page.
        """
        self._is_open = False
        self._is_read = False
        self._url = url
        self._data_table: list[EM27Property] = []
        pub.subscribe(self.request_data, "psf27.data.request")

    def open(self, timeout: int = 2) -> None:
        """Connect to the webpage.

        Args:
            timeout: Number of seconds to wait for response.
        """
        if not self._is_open:
            try:
                self._page = urlopen(self._url, timeout=timeout)
                self._is_open = True
                pub.sendMessage("psf27.opened")
                logging.info("Opened connection to automation units diagnostics page.")
            except HTTPError as e:
                self._error_occurred(e)
            except URLError as e:
                self._error_occurred(e)
            except TimeoutError as e:
                self._error_occurred(e)

    def close(self) -> None:
        """Disconnect from the webpage."""
        if self._is_open:
            self._page.close()
            self._is_open = False
            pub.sendMessage("psf27.closed")
            logging.info("Closed connection to automation units diagnostics page.")

    def read(self) -> None:
        """Read the webpage and store in EM27 object."""
        if self._is_open:
            self._html = self._page.read()
            self._is_read = True

    def get_psf27sensor_data(self) -> None:
        """Search for the PSF27Sensor table and store the data."""
        if self._is_read:
            html_text = self._html.decode("utf-8")
            table_header = (
                "<TR><TH>No</TH><TH>Name</TH><TH>Description</TH>"
                + "<TH>Status</TH><TH>Value</TH><TH>Meas. Unit</TH></TR>\n"
            )
            table_start = html_text.find(table_header)
            try:
                if table_start == -1:
                    raise PSF27Error("PSF27Sensor table not found")
            except Exception as e:
                self._error_occurred(e)
            else:
                table_end = table_start + html_text[table_start:].find("</TABLE>")
                table = html_text[table_start:table_end].splitlines()
                for row in range(1, len(table) - 1):
                    self._data_table.append(
                        EM27Property(
                            table[row].split("<TD>")[2].rstrip("</TD>"),
                            Decimal(table[row].split("<TD>")[5].strip("</TD>")),
                            table[row].split("<TD>")[6].rstrip("</TD></TR"),
                        )
                    )
                pub.sendMessage("psf27.data.send", data=table)

    def request_data(self) -> None:
        """Request the EM27 property data from the web server."""
        self.open()
        self.read()
        self.get_psf27sensor_data()
        self.close()

    def _error_occurred(self, exception: BaseException) -> None:
        """Log and communicate that an error occurred."""
        traceback_str = "".join(traceback.format_tb(exception.__traceback__))
        logging.error(f"Error during PSF27Sensor query: {traceback_str}")
        pub.sendMessage("psf27.error", message=str(exception))


class DummyEM27Scraper(EM27Scraper):
    """An interface for EM27 monitor testing."""

    def __init__(self) -> None:
        """Create a new monitor for a dummy EM27."""
        dummy_em27_fp = resources.files("finesse.hardware").joinpath("diag_autom.htm")
        super().__init__("file://" + str(dummy_em27_fp))


if __name__ == "__main__":
    dev = DummyEM27Scraper()
    dev.open()
    dev.read()
    dev.get_psf27sensor_data()
    for prop in dev._data_table:
        print(prop)
    dev.close()
