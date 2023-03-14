"""This module contains code for interfacing with different hardware devices."""
import sys

from pubsub import pub

if "--dummy-em27" in sys.argv:
    from .dummy_em27_diag_autom import DummyEM27Scraper as EM27Scraper
    from .dummy_opus import DummyOPUSInterface as OPUSInterface
else:
    from .em27_opus import OPUSInterface  # type: ignore
    from .em27_diag_autom import EM27Scraper  # type: ignore

from .dummy_stepper_motor import DummyStepperMotor

stepper: DummyStepperMotor
opus: OPUSInterface
scraper: EM27Scraper


def _init_hardware():
    global stepper, opus, scraper
    # TODO: Replace with a real stepper motor device
    stepper = DummyStepperMotor(3600)

    opus = OPUSInterface()
    scraper = EM27Scraper()


def _stop_hardware():
    global opus
    del opus


pub.subscribe(_init_hardware, "window.opened")
pub.subscribe(_stop_hardware, "window.closed")
