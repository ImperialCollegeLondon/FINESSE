"""Tests for EM27Scraper."""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from finesse.config import EM27_URL
from finesse.hardware.dummy_em27_scraper import DummyEM27Scraper
from finesse.hardware.em27_scraper import (
    EM27Property,
    EM27Scraper,
    PSF27Error,
    get_psf27sensor_data,
)


@pytest.fixture
def prop():
    """Fixture for EM27Property."""
    return EM27Property("Voltage", Decimal(1.23), "V")


def test_str(prop: EM27Property):
    """Test EM27Property's __str__() method."""
    assert prop.__str__() == "Voltage = 1.230000 V"


def test_val_str(prop: EM27Property):
    """Test EM27Property's val_str() method."""
    assert prop.val_str() == "1.230000 V"


@pytest.fixture
def dev():
    """Fixture for EM27Scraper."""
    return EM27Scraper()


@pytest.fixture
def dummy_dev():
    """Fixture for DummyEM27Scraper."""
    return DummyEM27Scraper()


def _get_em27_response(http_status_code: int) -> MagicMock:
    """Mock a requests.Response."""
    dev = dummy_dev()
    html = dev._read()
    response = MagicMock()
    response.status_code = (
        http_status_code  # 200: success, 404: not found, 408: timeout
    )
    if response.status_code == 200:
        response.content = html.encode()
    else:
        response.content = None
    return response


def test_init(dev: EM27Scraper):
    """Test EM27Scraper's __init__() method."""
    assert dev._url == EM27_URL


def test_read_success(dev: EM27Scraper):
    """Test EM27Scraper's _read() method."""
    dev._url = (
        "https://raw.githubusercontent.com/ImperialCollegeLondon/"
        + "FINESSE/em27_webscraper/finesse/hardware/diag_autom.htm"
    )
    content = dev._read()
    assert type(content) == str
    assert content.count("PSF27Sensor") == 1
    assert content.endswith("</HTML>\n")


@pytest.mark.parametrize(
    "url, timeout",
    [
        ("http://10.10.0.1/invalid.htm", float(2.0)),
        ("https://github.com/ImperialCollegeLondon/FINESSE/invalid.html", float(2.0)),
        (
            "https://raw.githubusercontent.com/ImperialCollegeLondon/"
            + "FINESSE/em27_webscraper/finesse/hardware/diag_autom.htm",
            1e-5,
        ),
    ],
)
def test_read_fail(dev: EM27Scraper, url: str, timeout: float):
    """Test failure of EM27Scraper's _read() method."""
    dev._url = url
    dev._timeout = timeout
    with pytest.raises(PSF27Error):
        content = dev._read()
        assert content is None


def test_get_psf27sensor_data_pass(dummy_dev: DummyEM27Scraper):
    """Test get_psf27sensor_data() function."""
    content = dummy_dev._read()
    data_table = get_psf27sensor_data(content)
    assert data_table != []
    assert len(data_table) == 7
    for row in data_table:
        assert type(row) == EM27Property


def test_get_psf27sensor_data_fail():
    """Test failure of get_psf27sensor_data() function."""
    content = "Not valid HTML"
    with pytest.raises(PSF27Error):
        data_table = get_psf27sensor_data(content)
        assert data_table == []


# def test_send_data(dev: EM27Scraper, sendmsg_mock: MagicMock):
#    """Test EM27Scraper's send_data() method."""
#    dev.send_data()
#    sendmsg_mock.assert_called("psf27.data.response")


def test_error_occurred(dev: EM27Scraper, sendmsg_mock: MagicMock):
    """Test EM27Scraper's _error_occurred() method."""
    dev._error_occurred(PSF27Error("Error occurred"))
    sendmsg_mock.assert_called_with("psf27.error", message="Error occurred")
