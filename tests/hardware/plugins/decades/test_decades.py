"""Tests for the Decades class."""

from unittest.mock import ANY, MagicMock, Mock, patch

import pytest
from PySide6.QtNetwork import QNetworkReply

from finesse.config import DECADES_QUERY_LIST, DECADES_URL
from finesse.hardware.plugins.decades.decades import (
    Decades,
    DecadesError,
)


@pytest.fixture
def decades(qtbot, subscribe_mock) -> Decades:
    """Fixture for Decades."""
    return Decades()


@patch("finesse.hardware.plugins.decades.decades.QTimer")
def test_init(qtimer_class_mock: Mock) -> None:
    """Test the Decades constructor."""
    sensors = Decades("1.2.3.4", 2.0)
    assert sensors._url == DECADES_URL.format(host="1.2.3.4")
    qtimer_mock = qtimer_class_mock.return_value
    qtimer_mock.timeout.connect.assert_called_once_with(sensors.send_data)
    qtimer_mock.start.assert_called_once_with(2000)


def test_close(decades: Decades) -> None:
    """Test the Decades close() method."""
    with patch.object(decades, "_poll_timer") as qtimer_mock:
        decades.close()
        qtimer_mock.stop.assert_called_once_with()


@patch("json.loads")
@patch("finesse.hardware.plugins.decades.decades.Decades._get_decades_data")
def test_on_reply_received_no_error(
    _get_decades_data_mock: Mock, json_loads_mock: Mock, decades: Decades, qtbot
) -> None:
    """Test the _on_reply_received() method works when no error occurs."""
    reply = MagicMock()
    reply.error.return_value = QNetworkReply.NetworkError.NoError

    # NB: This value is of the wrong type, but it doesn't matter for here
    _get_decades_data_mock.return_value = "cool_sensor_data"

    # Check the correct pubsub message is sent
    assert decades._on_reply_received(reply) == "cool_sensor_data"
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
@patch("finesse.hardware.plugins.decades.decades.Decades._get_decades_data")
def test_on_reply_received_exception(
    _get_decades_data_mock: Mock, json_loads_mock: Mock, decades: Decades, qtbot
) -> None:
    """Tests the _on_reply_received() method works when an exception is raised."""
    reply = MagicMock()
    reply.error.return_value = QNetworkReply.NetworkError.NoError

    # Make get_decades_data() raise an exception
    error = Exception()
    _get_decades_data_mock.side_effect = error

    with pytest.raises(Exception):
        # Check the correct pubsub message is sent
        decades._on_reply_received(reply)


def test_send_params(decades: Decades, qtbot) -> None:
    """Tests the send_data() method."""
    with patch.object(decades, "_requester") as requester_mock:
        with patch.object(decades, "pubsub_broadcast") as broadcast_mock:
            broadcast_mock.return_value = "WRAPPED_FUNC"
            decades.send_params()
            broadcast_mock.assert_called_once_with(
                decades._on_params_received, "params.response"
            )
            requester_mock.make_request.assert_called_once_with(ANY, "WRAPPED_FUNC")


def test_send_data(decades: Decades, qtbot) -> None:
    """Tests the send_data() method."""
    with patch.object(decades, "_requester") as requester_mock:
        with patch.object(decades, "pubsub_broadcast") as broadcast_mock:
            broadcast_mock.return_value = "WRAPPED_FUNC"
            decades.send_data()
            broadcast_mock.assert_called_once_with(
                decades._on_reply_received, "data.response", "data"
            )
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
        decades.send_data()
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
    data = decades._get_decades_data({"a": [1], "b": [2]})
    assert isinstance(data, list)
    assert len(data) == 2
    assert ["A", 1, ""] in data
    assert ["B", 2, ""] in data
