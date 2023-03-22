"""This module contains code for interfacing with different hardware devices."""
import sys

from pubsub import pub

if "--dummy-em27" in sys.argv:
    from .opus.dummy import DummyOPUSInterface as OPUSInterface
else:
    from .opus.em27 import OPUSInterface  # type: ignore

if "--dummy-tc4820" in sys.argv:
    from .temperature.dummy_temperature_controller import Decimal
    from .temperature.dummy_temperature_controller import (
        DummyTemperatureController as TC4820,
    )
    from .temperature.dummy_temperature_controller import NoiseParameters
else:
    from .temperature.tc4820 import TC4820  # type: ignore

from .stepper_motor.dummy import DummyStepperMotor

stepper: DummyStepperMotor
opus: OPUSInterface
tc4820_hot: TC4820
tc4820_cold: TC4820


def _init_hardware():
    global stepper, opus, tc4820_hot, tc4820_cold
    # TODO: Replace with a real stepper motor device
    stepper = DummyStepperMotor(3600)

    opus = OPUSInterface()
    tc4820_hot = TC4820(
        name="hot",
        temperature_params=NoiseParameters(35.0, 2.0, 123),
        power_params=NoiseParameters(40.0, 2.0, 123),
        initial_set_point=Decimal(70),
    )
    tc4820_cold = TC4820(
        name="cold",
        temperature_params=NoiseParameters(35.0, 2.0, 456),
        power_params=NoiseParameters(1.0, 0.1, 456),
        initial_set_point=Decimal(20),
    )


def _stop_hardware():
    global opus
    del opus


pub.subscribe(_init_hardware, "window.opened")
pub.subscribe(_stop_hardware, "window.closed")
