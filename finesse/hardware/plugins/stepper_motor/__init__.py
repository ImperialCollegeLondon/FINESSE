"""Code for interfacing with stepper motors."""
from typing import cast

from finesse.config import STEPPER_MOTOR_TOPIC
from finesse.device_info import DeviceInstanceRef
from finesse.hardware.devices import devices

from .stepper_motor_base import StepperMotorBase


def get_stepper_motor_instance() -> StepperMotorBase | None:
    """Get the instance of the current stepper motor device if connected or None."""
    try:
        return cast(StepperMotorBase, devices[DeviceInstanceRef(STEPPER_MOTOR_TOPIC)])
    except KeyError:
        return None
