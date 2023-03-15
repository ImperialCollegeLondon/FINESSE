"""Tests for EM27Scraper."""

from unittest.mock import MagicMock

import pytest
from pubsub import pub

from finesse.hardware.em27_scraper import EM27Property, EM27Scraper, PSF27Error


@pytest.fixture
def dev():
    """Fixture for EM27Scraper."""
    return EM27Scraper()


@pytest.fixture()
def send_message_mock(monkeypatch) -> MagicMock:
    """Magic Mock patched over pubsub.pub.sendMessage."""
    mock = MagicMock()
    monkeypatch.setattr(pub, "sendMessage", mock)
    return mock


def test_init(dev):
    """Test EM27Scraper's __init__() method."""
    assert dev._url == "http://10.10.0.1/diag_autom.htm"


def test_read(dev, send_message_mock):
    """Test EM27Scraper's read() method."""
    try:
        content = dev.read()
        assert dev._is_read
        assert type(content) == str
        assert content.count("PSF27Sensor") == 1
    except Exception:
        assert content == ""


def test_get_psf27sensor_data(dev):
    """Test EM27Scraper's get_psf27sensor_data() method."""
    content = dev.read()
    dev.get_psf27sensor_data(content)
    if dev._is_read:
        assert dev._data_table != []
        for row in dev._data_table:
            assert type(row) == EM27Property
    else:
        assert dev._data_table == []


def test_send_data(dev, send_message_mock):
    """Test EM27Scraper's send_data() method."""
    try:
        dev.send_data()
    except Exception:
        pass
    else:
        send_message_mock.assert_called_with(
            "psf27.data.response", data=dev._data_table
        )

    assert not dev._is_read


def test_error_occurred(dev, send_message_mock):
    """Test EM27Scraper's error_occurred() method."""
    try:
        raise PSF27Error("Error occurred")
    except PSF27Error as e:
        dev._error_occurred(e)
        send_message_mock.assert_called_with("psf27.error", message="Error occurred")
