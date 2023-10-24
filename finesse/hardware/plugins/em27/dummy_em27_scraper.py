"""This module provides an interface to a dummy EM27 monitor."""
from importlib import resources
from pathlib import Path

from .em27_scraper import EM27Scraper


class DummyEM27Scraper(EM27Scraper):
    """An interface for testing monitoring EM27 properties."""

    def __init__(self) -> None:
        """Create a new EM27 property monitor."""
        dummy_em27_fp = resources.files("finesse.hardware.plugins.em27").joinpath(
            "diag_autom.htm"
        )
        super().__init__(Path(str(dummy_em27_fp)).as_uri())
