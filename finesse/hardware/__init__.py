"""This module contains code for interfacing with different hardware devices."""
from pubsub import pub

from .dummy_stepper_motor import DummyStepperMotor
from .em27_opus import OPUSInterface

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
