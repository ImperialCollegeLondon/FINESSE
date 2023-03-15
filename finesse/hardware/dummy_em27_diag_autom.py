"""This module provides an interface to a dummy EM27 monitor."""
import logging
from importlib import resources

from .em27_diag_autom import EM27Scraper, PSF27Error


class DummyEM27Scraper(EM27Scraper):
    """An interface for testing monitoring EM27 properties."""

    def __init__(self) -> None:
        """Create a new EM27 property monitor.

        Args:
            url: Web address of the automation units diagnostics page.
        """
        dummy_em27_fp = resources.files("finesse.hardware").joinpath("diag_autom.htm")
        super().__init__(str(dummy_em27_fp))

    def read(self) -> str:
        """Read the webpage.

        Returns:
            content: html source read from the webpage
        """
        try:
            with open(self._url, "r") as page:
                content = page.read()
            self._is_read = True
            logging.info("Read PSF27Sensor table")
            return content
        except FileNotFoundError:
            self._is_read = False
            self._error_occurred(PSF27Error("Dummy EM27 server file not found"))
            return ""
