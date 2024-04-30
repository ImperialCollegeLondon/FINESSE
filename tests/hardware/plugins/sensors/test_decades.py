"""Tests for the Decades class."""

import json
from unittest.mock import ANY, MagicMock, Mock, patch

import pytest
from freezegun import freeze_time
from PySide6.QtNetwork import QNetworkReply

from finesse.config import DECADES_URL
from finesse.hardware.plugins.sensors.decades import (
    Decades,
    DecadesError,
    DecadesParameter,
)
from finesse.sensor_reading import SensorReading


@pytest.fixture
@patch("finesse.hardware.plugins.sensors.decades.HTTPRequester")
def decades(requester_mock, qtbot, subscribe_mock) -> Decades:
    """Fixture for Decades."""
    return Decades()


def test_init(qtbot) -> None:
    """Test the Decades constructor."""
    sensors = Decades("1.2.3.4", 2.0)
    assert sensors._url == DECADES_URL.format(host="1.2.3.4")


PARAMS = [DecadesParameter("a", "A", "m"), DecadesParameter("b", "B", "J")]
"""Example parameters."""


@patch("json.loads")
@patch("finesse.hardware.plugins.sensors.decades.Decades._get_decades_data")
def test_on_reply_received_no_error(
    get_decades_data_mock: Mock, json_loads_mock: Mock, decades: Decades
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


def test_on_reply_received_network_error(decades: Decades) -> None:
    """Tests the _on_reply_received() method works when a network error occurs."""
    reply = MagicMock()
    reply.error.return_value = QNetworkReply.NetworkError.HostNotFoundError
    reply.errorString.return_value = "Host not found"

    with pytest.raises(DecadesError):
        decades._on_reply_received(reply)


@patch("json.loads")
@patch("finesse.hardware.plugins.sensors.decades.Decades._get_decades_data")
def test_on_reply_received_exception(
    get_decades_data_mock: Mock, json_loads_mock: Mock, decades: Decades
) -> None:
    """Tests the _on_reply_received() method works when an exception is raised."""
    reply = MagicMock()
    reply.error.return_value = QNetworkReply.NetworkError.NoError

    # Make get_decades_data() raise an exception
    error = Exception()
    get_decades_data_mock.side_effect = error

    with pytest.raises(Exception):
        decades._on_reply_received(reply)


def test_obtain_parameter_list(decades: Decades) -> None:
    """Tests the obtain_parameter_list() method."""
    with patch.object(decades, "_requester") as requester_mock:
        with patch.object(decades, "pubsub_errors") as wrapper_mock:
            wrapper_mock.return_value = "WRAPPED_FUNC"
            decades.obtain_parameter_list()
            wrapper_mock.assert_called_once_with(decades._on_params_received)
            requester_mock.make_request.assert_called_once_with(ANY, "WRAPPED_FUNC")


@patch("finesse.hardware.plugins.sensors.decades.DECADES_QUERY_LIST", ["a", "b"])
def test_on_params_received_no_error(decades: Decades) -> None:
    """Test the _on_params_received() method."""
    assert not hasattr(decades, "_params")
    reply = MagicMock()
    reply.error.return_value = QNetworkReply.NetworkError.NoError
    raw_params = (
        {"ParameterName": "a", "DisplayText": "A", "DisplayUnits": "m"},
        {"ParameterName": "b", "DisplayText": "B", "DisplayUnits": "J"},
    )
    reply.readAll().data.return_value = json.dumps(raw_params).encode()

    with patch.object(decades, "start_polling") as start_mock:
        decades._on_params_received(reply)
        assert decades._params == PARAMS
        start_mock.assert_called_once_with()


def test_on_params_received_network_error(decades: Decades) -> None:
    """Test the _on_params_received() method when a network error occurs."""
    reply = MagicMock()
    reply.error.return_value = QNetworkReply.NetworkError.HostNotFoundError
    reply.errorString.return_value = "Host not found"

    with pytest.raises(DecadesError):
        decades._on_params_received(reply)


@freeze_time("1970-01-01 00:01:00")
def test_request_readings(decades: Decades) -> None:
    """Tests the request_readings() method."""
    decades._params = PARAMS
    with patch.object(decades, "_requester") as requester_mock:
        with patch.object(decades, "pubsub_errors") as wrapper_mock:
            wrapper_mock.return_value = "WRAPPED_FUNC"
            decades.request_readings()
            wrapper_mock.assert_called_once_with(decades._on_reply_received)
            query = decades._url + "/livedata?&frm=60&to=60&para=a&para=b"
            requester_mock.make_request.assert_called_once_with(query, "WRAPPED_FUNC")


def test_get_decades_data(decades: Decades) -> None:
    """Tests the get_decades_data() function on normal data."""
    decades._params = PARAMS
    data = decades._get_decades_data({"a": [1.0], "b": [2.0]})
    assert data == [SensorReading("A", 1.0, "m"), SensorReading("B", 2.0, "J")]
