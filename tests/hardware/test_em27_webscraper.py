"""Tests for the EM27Scraper class."""
from decimal import Decimal
from importlib import resources
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from PySide6.QtNetwork import QNetworkReply

from finesse.config import EM27_URL
from finesse.hardware.em27_scraper import (
    EM27Error,
    EM27Property,
    EM27Scraper,
    get_em27sensor_data,
)


@pytest.fixture
def em27_property():
    """Fixture for EM27Property."""
    return EM27Property("Voltage", Decimal(1.23), "V")


def test_str(em27_property: EM27Property):
    """Test EM27Property's __str__() method."""
    assert str(em27_property) == "Voltage = 1.230000 V"


def test_val_str(em27_property: EM27Property):
    """Test EM27Property's val_str() method."""
    assert em27_property.val_str() == "1.230000 V"


@pytest.fixture
def em27_scraper(qtbot) -> EM27Scraper:
    """Fixture for EM27Scraper."""
    return EM27Scraper()


def test_init(subscribe_mock: MagicMock) -> None:
    """Test EM27Scraper's constructor."""
    scraper = EM27Scraper()
    assert scraper._url == EM27_URL
    subscribe_mock.assert_called_once_with(scraper.send_data, "em27.data.request")


@patch("finesse.hardware.em27_scraper.get_em27sensor_data")
def test_on_reply_received_no_error(
    get_em27sensor_data_mock: Mock, em27_scraper: EM27Scraper, sendmsg_mock: Mock, qtbot
) -> None:
    """Test the _on_reply_received() method works when no error occurs."""
    reply = MagicMock()
    reply.error.return_value = QNetworkReply.NetworkError.NoError

    # NB: This value is of the wrong type, but it doesn't matter here
    get_em27sensor_data_mock.return_value = "EM27Properties"

    # Check the correct pubsub message is sent
    em27_scraper._on_reply_received(reply)
    sendmsg_mock.assert_called_once_with("em27.data.response", data="EM27Properties")


def test_on_reply_received_network_error(
    em27_scraper: EM27Scraper, sendmsg_mock: Mock, qtbot
) -> None:
    """Test the _on_reply_received() method works when a network error occurs."""
    reply = MagicMock()
    reply.error.return_value = QNetworkReply.NetworkError.HostNotFoundError
    reply.errorString.return_value = "Host not found"

    # Check the correct pubsub message is sent
    em27_scraper._on_reply_received(reply)
    assert sendmsg_mock.call_args.args[0] == "em27.error"
    assert isinstance(sendmsg_mock.call_args.kwargs["error"], EM27Error)
    assert (
        sendmsg_mock.call_args.kwargs["error"].args[0]
        == "Network error: Host not found"
    )


@patch("finesse.hardware.em27_scraper.get_em27sensor_data")
def test_on_reply_received_exception(
    get_em27sensor_data_mock: Mock, em27_scraper: EM27Scraper, sendmsg_mock: Mock, qtbot
) -> None:
    """Test the _on_reply_received() method works when an exception is raised."""
    reply = MagicMock()
    reply.error.return_value = QNetworkReply.NetworkError.NoError

    # Make get_em27sensor_data() raise an exception
    error = Exception()
    get_em27sensor_data_mock.side_effect = error

    # Check the correct pubsub message is sent
    em27_scraper._on_reply_received(reply)
    sendmsg_mock.assert_called_with("em27.error", error=error)


@patch("finesse.hardware.em27_scraper.QNetworkRequest")
def test_send_data(
    network_request_mock: Mock, em27_scraper: EM27Scraper, qtbot
) -> None:  # adapted from test_opus_interface's test_request_command()
    """Test EM27Scraper's send_data() method."""
    request = MagicMock()
    network_request_mock.return_value = request
    reply = MagicMock()

    with patch.object(em27_scraper, "_manager") as manager_mock:
        with patch.object(em27_scraper, "_on_reply_received") as reply_received_mock:
            manager_mock.get.return_value = reply
            em27_scraper.send_data()
            network_request_mock.assert_called_once_with(EM27_URL)
            request.setTransferTimeout.assert_called_once_with(
                round(1000 * em27_scraper._timeout)
            )

            # Check that the reply will be handled by _on_reply_received()
            connect_mock = reply.finished.connect
            connect_mock.assert_called_once()
            handler = connect_mock.call_args_list[0].args[0]
            handler()
            reply_received_mock.assert_called_once()


def test_get_em27sensor_data() -> None:
    """Test em27_scraper's get_em27sensor_data() function.

    Read in the snapshot of the EM27 webpage and ensure that
    the sensor data is correctly extracted from it.
    """
    dummy_em27_fp = resources.files("finesse.hardware").joinpath("diag_autom.htm")
    with dummy_em27_fp.open() as f:
        content = f.read()
    data_table = get_em27sensor_data(content)
    assert len(data_table) == 7
    for entry in data_table:
        assert isinstance(entry, EM27Property)


def test_get_em27sensor_data_no_table_found() -> None:
    """Test em27_scraper's get_em27sensor_data() function.

    Read in HTML content which does not contain a valid sensor data table
    to verify that an exception is raised.
    """
    content = "<HTML>No EM27 sensor data here</HTML>\n"
    with pytest.raises(EM27Error):
        get_em27sensor_data(content)
