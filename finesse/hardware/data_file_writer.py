"""Provides a class for writing sensor data to a CSV file."""
import logging
import os
import platform
from datetime import datetime
from decimal import Decimal
from math import floor
from pathlib import Path
from typing import Any

from csvy import Writer
from pubsub import pub

from .. import config
from ..event_counter import EventCounter
from .pubsub_decorators import pubsub_errors
from .stepper_motor import get_stepper_motor_instance
from .temperature import get_hot_bb_temperature_controller_instance


def _on_error_occurred(error: BaseException) -> None:
    """Close file in case of error."""
    pub.sendMessage("data_file.close")


def _get_platform_info() -> dict[str, str]:
    return {
        key: getattr(platform, key)() for key in ("platform", "python_version", "node")
    }


def _get_metadata(filename: str) -> dict[str, Any]:
    return {
        "encoding": "utf-8",
        "name": filename,
        "datetime": datetime.now().astimezone().isoformat(),  # include timezone
        "system": {
            "app": {
                "name": config.APP_NAME,
                "author": config.APP_AUTHOR,
                "version": config.APP_VERSION,
            },
            "platform": _get_platform_info(),
        },
    }


def _get_stepper_motor_angle() -> tuple[float, bool]:
    """Get the current angle of the stepper motor.

    This function returns a float indicating the angle in degrees and a boolean
    indicating whether the motor is currently moving. If an error occurs or the motor is
    moving, the angle returned will be nan.
    """
    stepper = get_stepper_motor_instance()

    # Stepper motor not connected
    if not stepper:
        return (float("nan"), False)

    try:
        if angle := stepper.angle:
            return (angle, False)
        else:
            return (float("nan"), True)
    except Exception as error:
        pub.sendMessage(f"serial.{config.STEPPER_MOTOR_TOPIC}.error", error=error)
        return (float("nan"), False)


def _get_hot_bb_power() -> float:
    """Get the current power of the hot BB temperature controller as a percentage.

    If an error occurs, nan will be returned.
    """
    hot_bb = get_hot_bb_temperature_controller_instance()

    # Hot BB temperature controller not connected
    if not hot_bb:
        return float("nan")

    try:
        return hot_bb.power * 100 / config.TC4820_MAX_POWER
    except Exception as error:
        pub.sendMessage(
            f"serial.{config.TEMPERATURE_CONTROLLER_TOPIC}.{hot_bb.name}.error",
            error=error,
        )
        return float("nan")


class DataFileWriter:
    """A class for writing sensor data to a CSV file.

    This class is a singleton. Every time a new file needs to be written this instance
    is reused.
    """

    def __init__(self) -> None:
        """Create a new DataFileWriter."""
        self._writer: Writer
        """The CSV writer."""

        self._enable_counter = EventCounter(
            self.enable,
            self.disable,
            device_names=(config.TEMPERATURE_MONITOR_TOPIC,),
        )

        # Listen to open/close messages
        pub.subscribe(self.open, "data_file.open")
        pub.subscribe(self.close, "data_file.close")

        # Close data file if GUI closes unexpectedly
        pub.subscribe(self.close, "window.closed")

        # Listen for error messages
        pub.subscribe(_on_error_occurred, "data_file.error")

    def enable(self) -> None:
        """Send enable message."""
        pub.sendMessage("data_file.enable")

    def disable(self) -> None:
        """Send disable message and close file if open."""
        pub.sendMessage("data_file.disable")
        pub.sendMessage("data_file.close")

    @pubsub_errors("data_file.error")
    def open(self, path: Path) -> None:
        """Open a file at the specified path for writing.

        Args:
            path: The path of the file to write to
        """
        logging.info(f"Opening data file at {path}")
        self._writer = Writer(path, _get_metadata(path.name))

        # Write column headers
        self._writer.writerow(
            (
                "Date",
                "Time",
                *(f"Temp{i+1}" for i in range(config.NUM_TEMPERATURE_MONITOR_CHANNELS)),
                "TimeAsSeconds",
                "Angle",
                "IsMoving",
                "TemperatureControllerPower",
            )
        )

        # Listen to temperature monitor messages
        pub.subscribe(
            self.write, f"serial.{config.TEMPERATURE_MONITOR_TOPIC}.data.response"
        )

    def close(self) -> None:
        """Close the current file handle."""
        pub.unsubscribe(
            self.write, f"serial.{config.TEMPERATURE_MONITOR_TOPIC}.data.response"
        )

        if hasattr(self, "_writer"):
            logging.info("Closing data file")

            # Ensure data is written to disk
            self._writer._file.flush()
            os.fsync(self._writer._file.fileno())

            self._writer.close()
            del self._writer

    @pubsub_errors("data_file.error")
    def write(self, time: datetime, temperatures: list[Decimal]) -> None:
        """Write temperature readings to the CSV file."""
        # Also include timestamp as seconds since midnight
        midnight = datetime(time.year, time.month, time.day)
        secs_since_midnight = floor((time - midnight).total_seconds())

        angle, is_moving = _get_stepper_motor_angle()
        self._writer.writerow(
            (
                time.strftime("%Y%m%d"),
                time.strftime("%H:%M:%S"),
                *temperatures,
                secs_since_midnight,
                angle,
                int(is_moving),
                _get_hot_bb_power(),
            )
        )
        self._writer._file.flush()


_data_file_writer = DataFileWriter()
"""The only instance of DataFileWriter."""
