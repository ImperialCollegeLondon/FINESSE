"""Tests for the EM27Sensors class."""

from decimal import Decimal
from importlib import resources
from unittest.mock import MagicMock, Mock, patch

import pytest
from PySide6.QtNetwork import QNetworkReply

from finesse.config import EM27_SENSORS_URL
from finesse.hardware.plugins.sensors.em27_sensors import (
    EM27Error,
    EM27Sensors,
    SensorReading,
    _on_reply_received,
    get_em27sensor_data,
)


@pytest.fixture
def sensor_reading():
    """Fixture for SensorReading."""
    return SensorReading("Voltage", Decimal(1.23), "V")


def test_str(sensor_reading: SensorReading):
    """Test SensorReading's __str__() method."""
    assert str(sensor_reading) == "Voltage = 1.230000 V"


def test_val_str(sensor_reading: SensorReading):
    """Test SensorReading's val_str() method."""
    assert sensor_reading.val_str() == "1.230000 V"


@pytest.fixture
def em27_sensors(qtbot, subscribe_mock) -> EM27Sensors:
    """Fixture for EM27Sensors."""
    return EM27Sensors()


def test_init() -> None:
    """Test EM27Sensors's constructor."""
    with patch("finesse.hardware.plugins.sensors.em27_sensors.QTimer") as qtimer_mock:
        qtimer = MagicMock()
        qtimer_mock.return_value = qtimer
        sensors = EM27Sensors("1.2.3.4", 2.0)
        assert sensors._url == EM27_SENSORS_URL.format(host="1.2.3.4")
        qtimer.timeout.connect.assert_called_once_with(sensors.send_data)
        qtimer.start.assert_called_once_with(2000)


def test_close(em27_sensors: EM27Sensors) -> None:
    """Test EM27Sensors' close() method."""
    with patch.object(em27_sensors, "_poll_timer") as qtimer_mock:
        em27_sensors.close()
        qtimer_mock.stop.assert_called_once_with()


@patch("finesse.hardware.plugins.sensors.em27_sensors.get_em27sensor_data")
def test_on_reply_received_no_error(get_em27sensor_data_mock: Mock, qtbot) -> None:
    """Test the _on_reply_received() method works when no error occurs."""
    reply = MagicMock()
    reply.error.return_value = QNetworkReply.NetworkError.NoError

    # NB: This value is of the wrong type, but it doesn't matter here
    get_em27sensor_data_mock.return_value = "sensor readings"

    # Check the correct pubsub message is sent
    assert _on_reply_received(reply) == "sensor readings"


def test_on_reply_received_network_error(qtbot) -> None:
    """Test the _on_reply_received() method works when a network error occurs."""
    reply = MagicMock()
    reply.error.return_value = QNetworkReply.NetworkError.HostNotFoundError
    reply.errorString.return_value = "Host not found"

    with pytest.raises(EM27Error):
        # Check the correct pubsub message is sent
        _on_reply_received(reply)


@patch("finesse.hardware.plugins.sensors.em27_sensors.get_em27sensor_data")
def test_on_reply_received_exception(get_em27sensor_data_mock: Mock, qtbot) -> None:
    """Test the _on_reply_received() method works when an exception is raised."""
    reply = MagicMock()
    reply.error.return_value = QNetworkReply.NetworkError.NoError

    # Make get_em27sensor_data() raise an exception
    error = Exception()
    get_em27sensor_data_mock.side_effect = error

    with pytest.raises(Exception):
        # Check the correct pubsub message is sent
        _on_reply_received(reply)


def test_send_data(em27_sensors: EM27Sensors, qtbot) -> None:
    """Test EM27Sensors's send_data() method."""
    with patch.object(em27_sensors, "_requester") as requester_mock:
        with patch.object(em27_sensors, "pubsub_broadcast") as broadcast_mock:
            broadcast_mock.return_value = "WRAPPED_FUNC"
            em27_sensors.send_data()
            broadcast_mock.assert_called_once_with(
                _on_reply_received, "data.response", "data"
            )
            requester_mock.make_request.assert_called_once_with(
                em27_sensors._url, "WRAPPED_FUNC"
            )


def test_get_em27sensor_data() -> None:
    """Test em27_sensors's get_em27sensor_data() function.

    Read in the snapshot of the EM27 webpage and ensure that
    the sensor data is correctly extracted from it.
    """
    dummy_em27_fp = resources.files("finesse.hardware.plugins.sensors").joinpath(
        "diag_autom.htm"
    )
    with dummy_em27_fp.open() as f:
        content = f.read()
    data_table = get_em27sensor_data(content)
    assert len(data_table) == 7
    for entry in data_table:
        assert isinstance(entry, SensorReading)


def test_get_em27sensor_data_no_table_found() -> None:
    """Test em27_sensors's get_em27sensor_data() function.

    Read in HTML content which does not contain a valid sensor data table
    to verify that an exception is raised.
    """
    content = "<HTML>No EM27 sensor data here</HTML>\n"
    with pytest.raises(EM27Error):
        get_em27sensor_data(content)
