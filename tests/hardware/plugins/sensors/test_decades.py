"""Tests for the Decades class."""

from unittest.mock import ANY, MagicMock, Mock, patch

import pytest
from PySide6.QtNetwork import QNetworkReply

from finesse.config import DECADES_QUERY_LIST, DECADES_URL
from finesse.hardware.plugins.sensors.decades import (
    Decades,
    DecadesError,
)
from finesse.sensor_reading import SensorReading


@pytest.fixture
def decades(qtbot, subscribe_mock) -> Decades:
    """Fixture for Decades."""
    return Decades()


def test_init(qtbot) -> None:
    """Test the Decades constructor."""
    sensors = Decades("1.2.3.4", 2.0)
    assert sensors._url == DECADES_URL.format(host="1.2.3.4")


@patch("json.loads")
@patch("finesse.hardware.plugins.sensors.decades.Decades._get_decades_data")
def test_on_reply_received_no_error(
    get_decades_data_mock: Mock, json_loads_mock: Mock, decades: Decades, qtbot
) -> None:
    """Test the _on_reply_received() method works when no error occurs."""
    reply = MagicMock()
    reply.error.return_value = QNetworkReply.NetworkError.NoError

    # NB: This value is of the wrong type, but it doesn't matter for here
    get_decades_data_mock.return_value = "cool_sensor_data"

    # Check the correct pubsub message is sent
    with patch.object(decades, "send_readings_message") as send_readings_mock:
        decades._on_reply_received(reply)
        send_readings_mock.assert_called_once_with("cool_sensor_data")
        json_loads_mock.assert_called_once_with(reply.readAll().data().decode())


def test_on_reply_received_network_error(decades: Decades, qtbot) -> None:
    """Tests the _on_reply_received() method works when a network error occurs."""
    reply = MagicMock()
    reply.error.return_value = QNetworkReply.NetworkError.HostNotFoundError
    reply.errorString.return_value = "Host not found"

    with pytest.raises(DecadesError):
        # Check the correct pubsub message is sent
        decades._on_reply_received(reply)


@patch("json.loads")
@patch("finesse.hardware.plugins.sensors.decades.Decades._get_decades_data")
def test_on_reply_received_exception(
    get_decades_data_mock: Mock, json_loads_mock: Mock, decades: Decades, qtbot
) -> None:
    """Tests the _on_reply_received() method works when an exception is raised."""
    reply = MagicMock()
    reply.error.return_value = QNetworkReply.NetworkError.NoError

    # Make get_decades_data() raise an exception
    error = Exception()
    get_decades_data_mock.side_effect = error

    with pytest.raises(Exception):
        # Check the correct pubsub message is sent
        decades._on_reply_received(reply)


def test_send_params(decades: Decades, qtbot) -> None:
    """Tests the send_data() method."""
    with patch.object(decades, "_requester") as requester_mock:
        with patch.object(decades, "pubsub_errors") as wrapper_mock:
            wrapper_mock.return_value = "WRAPPED_FUNC"
            decades.obtain_parameter_list()
            wrapper_mock.assert_called_once_with(decades._on_params_received)
            requester_mock.make_request.assert_called_once_with(ANY, "WRAPPED_FUNC")


def test_send_data(decades: Decades, qtbot) -> None:
    """Tests the send_data() method."""
    with patch.object(decades, "_requester") as requester_mock:
        with patch.object(decades, "pubsub_errors") as wrapper_mock:
            wrapper_mock.return_value = "WRAPPED_FUNC"
            decades.request_readings()
            wrapper_mock.assert_called_once_with(decades._on_reply_received)
            requester_mock.make_request.assert_called_once_with(ANY, "WRAPPED_FUNC")


@patch("time.time")
def test_send_data_query(time_mock: Mock, decades: Decades, qtbot) -> None:
    """Tests the send_data() method."""
    with patch.object(decades, "_requester") as requester_mock:
        decades._url = "http://localhost/test"
        time_mock.return_value = 999
        DECADES_QUERY_LIST.clear()
        DECADES_QUERY_LIST.append("a")
        DECADES_QUERY_LIST.append("b")
        decades.request_readings()
        query = decades._url + "/livedata?&frm=999&to=999&para=a&para=b"
        requester_mock.make_request.assert_called_once_with(query, ANY)


def test_get_decades_data(decades: Decades) -> None:
    """Tests the get_decades_data() function on normal data."""
    DECADES_QUERY_LIST.clear()
    DECADES_QUERY_LIST.append("a")
    DECADES_QUERY_LIST.append("b")
    decades._params = [
        {"ParameterName": "a", "DisplayText": "A", "DisplayUnits": ""},
        {"ParameterName": "b", "DisplayText": "B", "DisplayUnits": ""},
    ]
    data = decades._get_decades_data({"a": [1.0], "b": [2.0]})
    assert data == [SensorReading("A", 1.0, ""), SensorReading("B", 2.0, "")]
