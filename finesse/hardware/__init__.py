"""This module contains code for interfacing with different hardware devices."""
import sys

from pubsub import pub

if "--dummy-em27" in sys.argv:
    from .opus.dummy import DummyOPUSInterface as OPUSInterface
else:
    from .opus.em27 import OPUSInterface  # type: ignore

from .stepper_motor import create_stepper_motor_serial_manager
from .temperature import create_temperature_controller_serial_managers

opus: OPUSInterface


def _init_hardware():
    global opus

    opus = OPUSInterface()


def _stop_hardware():
    global opus
    del opus


pub.subscribe(_init_hardware, "window.opened")
pub.subscribe(_stop_hardware, "window.closed")

create_stepper_motor_serial_manager()
create_temperature_controller_serial_managers()

# HACK: Temporary workaround so that we can use dummy devices for now
pub.sendMessage("serial.stepper_motor.open", port="Dummy", baudrate=-1)
pub.sendMessage("serial.temperature_controller.hot_bb.open", port="Dummy", baudrate=-1)
pub.sendMessage("serial.temperature_controller.cold_bb.open", port="Dummy", baudrate=-1)
