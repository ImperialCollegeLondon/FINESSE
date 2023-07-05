"""Tests for the EM27Scraper class."""
from unittest.mock import MagicMock

from finesse.config import EM27_URL
from finesse.hardware.em27_scraper import EM27Scraper


def test_init(subscribe_mock: MagicMock) -> None:
    """Test EM27Scraper's constructor."""
    scraper = EM27Scraper(EM27_URL)
    subscribe_mock.assert_any_call(scraper.send_data, "em27.data.request")


def test_send_data():
    """Test EM27Scraper's send_data() method."""
    raise NotImplementedError
