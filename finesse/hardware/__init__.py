"""This module contains code for interfacing with different hardware devices."""
import sys

from pubsub import pub

if "--dummy-em27" in sys.argv:
    from .opus.dummy import DummyOPUSInterface as OPUSInterface
else:
    from .opus.em27 import OPUSInterface  # type: ignore

from .stepper_motor import create_stepper_motor_serial_manager
from .temperature import create_temperature_controller_serial_managers

if "--dummy-dp9800" in sys.argv:
    from .temperature.dummy_dp9800 import DummyDP9800 as DP9800
else:
    from .temperature.dp9800 import DP9800  # type: ignore

dp9800: DP9800
opus: OPUSInterface


def _init_hardware():
    global opus, dp9800

    opus = OPUSInterface()

    dp9800 = DP9800()


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
