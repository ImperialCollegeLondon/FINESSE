"""This module provides an interface to the EM27 monitor.

This is used to scrape the PSF27 sensor data table off the server.
"""
import logging
from dataclasses import dataclass
from decimal import Decimal

from pubsub import pub
from requests import get
from requests.exceptions import ConnectionError, HTTPError, Timeout

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
        self._url: str = url
        self._timeout: int = 2
        self._data_table: list[EM27Property] = []

        pub.subscribe(self.send_data, "psf27.data.request")

    def _read(self) -> str:
        """Read the webpage.

        Returns:
            content: html source read from the webpage
        """
        try:
            request = get(self._url, timeout=self._timeout)

            # Check whether an error occured
            request.raise_for_status()

            content = request.text
            logging.info("Read PSF27Sensor table")
            return content
        except ConnectionError:
            raise PSF27Error(f"Error connecting to {self._url}")
        except HTTPError:
            raise PSF27Error(f"{self._url} not found")
        except Timeout:
            raise PSF27Error("Request timed out")

    def _get_psf27sensor_data(self, content: str) -> None:
        """Search for the PSF27Sensor table and store the data."""
        table_header = (
            "<TR><TH>No</TH><TH>Name</TH><TH>Description</TH>"
            + "<TH>Status</TH><TH>Value</TH><TH>Meas. Unit</TH></TR>\n"
        )
        table_start = content.find(table_header)
        if table_start == -1:
            raise PSF27Error("PSF27Sensor table not found")
        else:
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
            self._data_table = data_table

    def send_data(self) -> None:
        """Request the EM27 property data from the web server and send to GUI."""
        try:
            content = self._read()
            self._get_psf27sensor_data(content)
        except PSF27Error as e:
            self._error_occurred(e)

        pub.sendMessage("psf27.data.response", data=self._data_table)

    def _error_occurred(self, exception: BaseException) -> None:
        """Log and communicate that an error occurred."""
        logging.error(f"Error during PSF27Sensor query:\t{exception}")
        pub.sendMessage("psf27.error", message=str(exception))
