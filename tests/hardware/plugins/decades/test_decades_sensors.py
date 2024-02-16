"""Tests for the DecadesSensors class."""
from unittest.mock import ANY, MagicMock, Mock, patch

import pytest
from PySide6.QtNetwork import QNetworkReply

from finesse.config import DECADES_SENSORS_QUERY_LIST, DECADES_SENSORS_URL
from finesse.hardware.plugins.decades.decades_sensors import (
    DecadesError,
    DecadesSensors,
    _on_reply_received,
    get_decades_sensor_data,
)


@pytest.fixture
def decades_sensors(qtbot, subscribe_mock) -> DecadesSensors:
    """Fixture for DecadesSensors."""
    return DecadesSensors()


@patch("finesse.hardware.plugins.decades.decades_sensors.QTimer")
def test_init(qtimer_class_mock: Mock) -> None:
    """Test DecadesSensors's constructor."""
    sensors = DecadesSensors("1.2.3.4", 2.0)
    assert sensors._url == DECADES_SENSORS_URL.format(host="1.2.3.4")
    qtimer_mock = qtimer_class_mock.return_value
    qtimer_mock.timeout.connect.assert_called_once_with(sensors.send_data)
    qtimer_mock.start.assert_called_once_with(2000)


def test_close(decades_sensors: DecadesSensors) -> None:
    """Test DecadesSensors' close() method."""
    with patch.object(decades_sensors, "_poll_timer") as qtimer_mock:
        decades_sensors.close()
        qtimer_mock.stop.assert_called_once_with()


@patch("json.loads")
@patch("finesse.hardware.plugins.decades.decades_sensors.get_decades_sensor_data")
def test_on_reply_received_no_error(
    get_decades_sensor_data_mock: Mock, json_loads_mock: Mock, qtbot
) -> None:
    """Test the _on_reply_received() method works when no error occurs."""
    reply = MagicMock()
    reply.error.return_value = QNetworkReply.NetworkError.NoError

    # NB: This value is of the wrong type, but it doesn't matter for here
    get_decades_sensor_data_mock.return_value = "cool_sensor_data"

    # Check the correct pubsub message is sent
    assert _on_reply_received(reply) == "cool_sensor_data"
    json_loads_mock.assert_called_once_with(reply.readAll().data().decode())


def test_on_reply_received_network_error(qtbot) -> None:
    """Tests the _on_reply_received() method works when a network error occurs."""
    reply = MagicMock()
    reply.error.return_value = QNetworkReply.NetworkError.HostNotFoundError
    reply.errorString.return_value = "Host not found"

    with pytest.raises(DecadesError):
        # Check the correct pubsub message is sent
        _on_reply_received(reply)


@patch("json.loads")
@patch("finesse.hardware.plugins.decades.decades_sensors.get_decades_sensor_data")
def test_on_reply_received_exception(
    get_decades_sensor_data_mock: Mock, json_loads_mock: Mock, qtbot
) -> None:
    """Tests the _on_reply_received() method works when an exception is raised."""
    reply = MagicMock()
    reply.error.return_value = QNetworkReply.NetworkError.NoError

    # Make get_decades_sensor_data() raise an exception
    error = Exception()
    get_decades_sensor_data_mock.side_effect = error

    with pytest.raises(Exception):
        # Check the correct pubsub message is sent
        _on_reply_received(reply)


def test_send_data(decades_sensors: DecadesSensors, qtbot) -> None:
    """Tests the send_data() method."""
    with patch.object(decades_sensors, "_requester") as requester_mock:
        with patch.object(decades_sensors, "pubsub_broadcast") as broadcast_mock:
            broadcast_mock.return_value = "WRAPPED_FUNC"
            decades_sensors.send_data()
            broadcast_mock.assert_called_once_with(
                _on_reply_received, "data.response", "data"
            )
            requester_mock.make_request.assert_called_once_with(ANY, "WRAPPED_FUNC")


@patch("time.time")
def test_send_data_query(
    time_mock: Mock, decades_sensors: DecadesSensors, qtbot
) -> None:
    """Tests the send_data() method."""
    with patch.object(decades_sensors, "_requester") as requester_mock:
        decades_sensors._url = "http://localhost/test"
        time_mock.return_value = 999
        DECADES_SENSORS_QUERY_LIST.clear()
        DECADES_SENSORS_QUERY_LIST.append("a")
        DECADES_SENSORS_QUERY_LIST.append("b")
        decades_sensors.send_data()
        query = decades_sensors._url + "?&frm=999&to=999&para=a&para=b"
        requester_mock.make_request.assert_called_once_with(query, ANY)


def test_get_decades_sensor_data() -> None:
    """Tests the get_decades_sensor_data() function on normal data."""
    data = get_decades_sensor_data({"a": [1], "b": [2]})
    assert isinstance(data, dict)
    assert len(data) == 2
    assert "a" in data
    assert data["a"] == 1
    assert "b" in data
    assert data["b"] == 2


def test_get_decades_sensor_unexpected_data() -> None:
    """Tests the get_decades_sensor_data() function on unexpected data."""
    with pytest.raises(DecadesError):
        get_decades_sensor_data({"a": []})
        get_decades_sensor_data({"b": [1, 2]})
