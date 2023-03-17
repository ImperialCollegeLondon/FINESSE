"""This module provides an interface to a dummy EM27 monitor."""
import logging
from importlib import resources

from .em27_scraper import EM27Scraper, PSF27Error


class DummyEM27Scraper(EM27Scraper):
    """An interface for testing monitoring EM27 properties."""

    def __init__(self) -> None:
        """Create a new EM27 property monitor."""
        dummy_em27_fp = resources.files("finesse.hardware").joinpath("diag_autom.htm")
        super().__init__(str(dummy_em27_fp))

    def _read(self) -> str:
        """Read the webpage.

        Returns:
            content: html source read from the webpage
        """
        try:
            with open(self._url, "r") as page:
                content = page.read()
            logging.info("Read PSF27Sensor table")
            return content
        except FileNotFoundError:
            raise PSF27Error(f"Dummy EM27 server file {self._url} not found")
