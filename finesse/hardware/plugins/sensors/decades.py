"""This module provides an interface to the DECADES API.

This is used to query the DECADES server for aircraft sensor data.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QUrlQuery, Slot
from PySide6.QtNetwork import QNetworkReply

from finesse.config import DECADES_HOST, DECADES_POLL_INTERVAL, DECADES_URL
from finesse.hardware.http_requester import HTTPRequester
from finesse.hardware.plugins.sensors.sensors_base import SensorsBase
from finesse.sensor_reading import SensorReading


class DecadesError(Exception):
    """Indicates that an error occurred while querying the DECADES server."""


@dataclass
class DecadesParameter:
    """Represents a parameter returned from the DECADES server."""

    name: str
    """Short name for the parameter."""
    readable_name: str
    """Human-readable name."""
    unit: str
    """Unit for the value."""

    def get_sensor_reading(self, value: float) -> SensorReading:
        """Get a SensorReading object with specified value for this parameter."""
        return SensorReading(self.readable_name, value, self.unit)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DecadesParameter:
        """Create a DecadesParameter from a dict."""
        return DecadesParameter(d["ParameterName"], d["DisplayText"], d["DisplayUnits"])


class Decades(
    SensorsBase,
    description="DECADES sensors",
    parameters={
        "host": "The IP address or hostname of the DECADES server",
    },
):
    """A class for monitoring a DECADES sensor server."""

    def __init__(
        self,
        host: str = DECADES_HOST,
        poll_interval: float = DECADES_POLL_INTERVAL,
    ) -> None:
        """Create a new Decades instance.

        Args:
            host: The IP address or hostname of the DECADES server
            poll_interval: How often to poll the sensors (seconds)
        """
        self._url: str = DECADES_URL.format(host=host)
        self._requester = HTTPRequester()
        self._params: list[DecadesParameter]
        """Parameters returned by the server."""

        # Obtain full parameter list in order to parse received data
        self.obtain_parameter_list()

        # We only want to start polling after we have loaded the parameter list
        super().__init__(poll_interval, start_polling=False)

    def obtain_parameter_list(self) -> None:
        """Request the parameter list from the DECADES server and wait for response."""
        self._requester.make_request(
            self._url + "/params/availability",
            self.pubsub_errors(self._on_params_received),
        )

    def request_readings(self) -> None:
        """Request the sensor data from the DECADES server.

        The HTTP request is made on a background thread.
        """
        epoch_time = str(int(time.time()))
        url = QUrlQuery(self._url + "/livedata?")
        url.addQueryItem("frm", epoch_time)
        url.addQueryItem("to", epoch_time)
        for param in self._params:
            url.addQueryItem("para", param.name)

        self._requester.make_request(
            url.toString(), self.pubsub_errors(self._on_reply_received)
        )

    def _get_decades_data(self, content: dict[str, list]) -> Iterable[SensorReading]:
        """Parse and return sensor data from a DECADES server query.

        Args:
            content: The content of the HTTP response from the DECADES server

        Returns:
            A list of sensor readings.
        """
        for param in self._params:
            try:
                if values := content[param.name]:
                    yield param.get_sensor_reading(values[-1])
            except KeyError:
                logging.warn(
                    f"DECADES: Server did not return data for parameter {param.name}"
                )

    @Slot()
    def _on_reply_received(self, reply: QNetworkReply) -> None:
        """Handle received HTTP reply.

        Args:
            reply: the response from the server
        """
        if reply.error() != QNetworkReply.NetworkError.NoError:
            raise DecadesError(f"Error: {reply.errorString()}")
        content = json.loads(reply.readAll().data().decode())
        readings = tuple(self._get_decades_data(content))
        self.send_readings_message(readings)

    def _on_params_received(self, reply: QNetworkReply) -> None:
        """Handle received HTTP reply.

        Args:
            reply: the response from the server
        """
        if reply.error() != QNetworkReply.NetworkError.NoError:
            raise DecadesError(f"Error: {reply.errorString()}")

        content = json.loads(reply.readAll().data().decode())
        self._params = [
            DecadesParameter.from_dict(param) for param in content if param["available"]
        ]

        # Now we have enough information to start parsing sensor readings
        self.start_polling()
