"""Code for interfacing with stepper motors."""

from finesse.hardware.manage_devices import get_device_instance

from .stepper_motor_base import StepperMotorBase


def get_stepper_motor_instance() -> StepperMotorBase | None:
    """Get the instance of the current stepper motor device if connected or None."""
    return get_device_instance(StepperMotorBase)
