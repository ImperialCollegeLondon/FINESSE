"""Tests for DummyEM27Scraper."""

import pytest

from finesse.hardware.dummy_em27_scraper import DummyEM27Scraper, PSF27Error


@pytest.fixture
def dev():
    """Fixture for DummyEM27Scraper."""
    return DummyEM27Scraper()


def test_init(dev):
    """Test DummyEM27Scraper's __init__() method."""
    unix_path = "finesse/hardware/diag_autom.htm"
    win_path = "finesse\\hardware\\diag_autom.htm"
    assert (dev._url.count(unix_path) == 1) ^ (dev._url.count(win_path) == 1)


def test_read_pass(dev):
    """Test success of DummyEM27Scraper's _read() method."""
    content = dev._read()
    assert type(content) == str
    assert content.count("PSF27Sensor") == 1
    assert content.endswith("</HTML>\n")


def test_read_fail(dev):
    """Test failure of DummyEM27Scraper's _read() method."""
    dev._url += "chars"
    with pytest.raises(PSF27Error):
        content = dev._read()
        assert content is None
