"""This module provides an interface to the EM27 monitor.

This is used to scrape the data table off the server.
"""
from typing import Dict, Tuple
from urllib.request import urlopen


class EM27:
    """An interface for EM27 monitoring."""

    def __init__(self, url: str = "http://10.10.0.1/diag_autom.htm") -> None:
        """Create a new EM27 monitor.

        Args:
            url: "Web address of the automation units diagnostics page.
        """
        # "file:///home/dc2917/Downloads/Automation units Diagnostics.html"
        self._url = url
        self._data_table: Dict[str, Tuple[float, str]] = {}

    def open(self):
        """Connect to the webpage."""
        self._page = urlopen(self._url)

    def close(self):
        """Disconnect from the webpage."""
        self._page.close()

    def read(self):
        """Read the webpage, search for the table and store the data."""
        html_bytes = self._page.read()
        html = html_bytes.decode("utf-8")
        table_header = (
            "<TR><TH>No</TH><TH>Name</TH><TH>Description</TH>"
            + "<TH>Status</TH><TH>Value</TH><TH>Meas. Unit</TH></TR>\n"
            # "<tbody><tr><th>No</th><th>Name</th><th>Description</th>"
            # + "<th>Status</th><th>Value</th><th>Meas. Unit</th></tr>\n"
        )
        table_start = html.find(table_header)
        if table_start == -1:
            print("Error: table not located")
            print(html)
            return
        table_end = table_start + html[table_start:].find("</TABLE>")
        table = html[table_start:table_end].splitlines()
        for row in range(1, len(table) - 1):
            self._data_table[table[row].split("<TD>")[2].rstrip("</TD>")] = (
                float(table[row].split("<TD>")[5].strip("</TD>")),
                table[row].split("<TD>")[6].rstrip("</TD></TR"),
            )


if __name__ == "__main__":

    dev = EM27()
    dev.open()
    dev.read()
    print(dev._data_table)
    dev.close()
