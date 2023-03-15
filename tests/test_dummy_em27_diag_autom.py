"""Tests for DummyEM27Scraper."""

import pytest

from finesse.hardware.dummy_em27_diag_autom import DummyEM27Scraper


@pytest.fixture
def dev():
    """Fixture for DummyEM27Scraper."""
    return DummyEM27Scraper()


def test_init(dev):
    """Test DummyEM27Scraper's __init__() method."""
    assert dev._url.count("finesse/hardware/diag_autom.htm") == 1


def test_read_fail(dev):
    """Test failure of DummyEM27Scraper's read() method."""
    dev._url = dev._url + "chars"
    try:
        content = dev.read()
        assert dev._is_read
        assert type(content) == str
        assert content.count("PSF27Sensor") == 1
    except Exception:
        assert content == ""
