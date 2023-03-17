"""This module contains code for interfacing with different hardware devices."""
import sys

from pubsub import pub

if "--dummy-em27" in sys.argv:
    from .opus.dummy import DummyOPUSInterface as OPUSInterface
else:
    from .opus.em27 import OPUSInterface  # type: ignore

from .stepper_motor.dummy import DummyStepperMotor

stepper: DummyStepperMotor
opus: OPUSInterface


def _init_hardware():
    global stepper, opus
    # TODO: Replace with a real stepper motor device
    stepper = DummyStepperMotor(3600)

    opus = OPUSInterface()


def _stop_hardware():
    global opus
    del opus


pub.subscribe(_init_hardware, "window.opened")
pub.subscribe(_stop_hardware, "window.closed")
