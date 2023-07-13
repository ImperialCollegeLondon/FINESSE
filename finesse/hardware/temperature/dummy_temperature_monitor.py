"""This module provides an interface to dummy DP9800 temperature readers."""
from decimal import Decimal
from typing import Sequence

from ...config import NUM_TEMPERATURE_MONITOR_CHANNELS
from ..noise_producer import NoiseParameters
from .temperature_monitor_base import TemperatureMonitorBase

_BASE_TEMPS = (19, 17, 26, 22, 24, 68, 69, 24)
"""The mean temperatures for each of the channels."""

_DEFAULT_TEMP_PARAMS = [NoiseParameters(mean=temp, seed=None) for temp in _BASE_TEMPS]
"""The default random parameters.

A random seed is used."""


class DummyTemperatureMonitor(TemperatureMonitorBase):
    """A dummy temperature monitor for GUI testing."""

    def __init__(
        self, temperature_params: Sequence[NoiseParameters] = _DEFAULT_TEMP_PARAMS
    ) -> None:
        """Create a new DummyTemperatureMonitor."""
        if len(temperature_params) != NUM_TEMPERATURE_MONITOR_CHANNELS:
            raise ValueError(
                f"Must provide {NUM_TEMPERATURE_MONITOR_CHANNELS} parameters"
            )

        super().__init__("dummy")
        self._temperature_producers = [
            params.create_producer(type=Decimal) for params in temperature_params
        ]

    def close(self) -> None:
        """Close the connection to the device."""

    def get_temperatures(self) -> list[Decimal]:
        """Get current temperatures."""
        return [producer() for producer in self._temperature_producers]
