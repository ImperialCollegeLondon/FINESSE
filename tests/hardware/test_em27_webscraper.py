"""Tests for the EM27Scraper class."""
from importlib import resources
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from finesse.config import EM27_URL
from finesse.hardware.em27_scraper import EM27Property, EM27Scraper, get_em27sensor_data


@pytest.fixture
def em27_scraper(qtbot) -> EM27Scraper:
    """Fixture for EM27Scraper."""
    return EM27Scraper()


def test_init(
    subscribe_mock: MagicMock,
) -> None:  # adapted from test_data_file_writer's test_init()
    """Test EM27Scraper's constructor."""
    scraper = EM27Scraper()
    subscribe_mock.assert_any_call(scraper.send_data, "em27.data.request")


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
    with open(Path(str(dummy_em27_fp)), "r") as f:
        content = f.read()
    data_table = get_em27sensor_data(content)
    assert len(data_table) == 7
    for entry in data_table:
        assert type(entry) == EM27Property
