"""Provides a dummy TC4820 device."""
from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from typing import Any

from .noise_producer import NoiseProducer
from .tc4820_base import TC4820Base


def alarm_status_ok(*args: Any, **kwargs: Any) -> int:
    """Signals that the alarm status is OK."""
    return 0


class DummyTC4820(TC4820Base):
    """A dummy TC4820 device which allows for setting custom mock attributes.

    Temperature, power and alarm status can be configured to produce custom results
    (defaulting to random noise). The set point is a simple field whose value can be
    get/set as usual.
    """

    _instance_exists = False

    temperature: property
    power: property
    alarm_status: property

    def __init__(
        self,
        temperature_producer: Callable[[], Decimal] = NoiseProducer(35.0, 2.0, Decimal),
        power_producer: Callable[[], int] = NoiseProducer(40.0, 2.0, int),
        alarm_status_producer: Callable[[], int] = alarm_status_ok,
        initial_set_point: Decimal = Decimal(70),
    ) -> None:
        """Create a new DummyTC4820.

        Note that because of how properties work in Python, only a single instance of
        this class can be created.

        Args:
            temperature_producer: Function returning temperature
            power_producer: Function returning power
            alarm_status_producer: Function returning alarm status (0 means "OK")
            initial_set_point: What the temperature set point is initially
        """
        assert not self._instance_exists
        self._instance_exists = True

        # Properties have to be assigned to classes rather than objects
        DummyTC4820.temperature = property(temperature_producer)  # type: ignore
        DummyTC4820.power = property(power_producer)  # type: ignore
        DummyTC4820.alarm_status = property(alarm_status_producer)  # type: ignore

        self.set_point = initial_set_point

        super().__init__()

    def __del__(self) -> None:
        """Reset the flag so a new instance can be created."""
        self._instance_exists = False
