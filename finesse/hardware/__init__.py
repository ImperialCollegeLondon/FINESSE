"""This module contains code for interfacing with different hardware devices."""
from .dummy_stepper_motor import DummyStepperMotor

# TODO: Replace with a real stepper motor device
stepper = DummyStepperMotor(3600)
