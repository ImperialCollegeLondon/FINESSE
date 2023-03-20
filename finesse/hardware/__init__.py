"""This module contains code for interfacing with different hardware devices."""
import sys

from pubsub import pub

if "--dummy-em27" in sys.argv:
    from .opus.dummy import DummyOPUSInterface as OPUSInterface
else:
    from .opus.em27 import OPUSInterface  # type: ignore

if "--dummy-dp9800" in sys.argv:
    from .dummy_dp9800 import DummyDP9800 as DP9800
else:
    from .dp9800 import DP9800  # type: ignore

from .stepper_motor.dummy import DummyStepperMotor

dp9800: DP9800
stepper: DummyStepperMotor
opus: OPUSInterface


def _init_hardware():
    global stepper, opus, dp9800
    # TODO: Replace with a real stepper motor device
    stepper = DummyStepperMotor(3600)

    opus = OPUSInterface()

    dp9800 = DP9800()


def _stop_hardware():
    global opus
    del opus


pub.subscribe(_init_hardware, "window.opened")
pub.subscribe(_stop_hardware, "window.closed")
