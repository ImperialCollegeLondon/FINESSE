"""Provides a class for writing sensor data to a CSV file."""
import platform
from datetime import datetime
from decimal import Decimal
from math import floor
from pathlib import Path
from typing import Any

from csvy import Writer
from pubsub import pub

from .. import config
from .pubsub_decorators import pubsub_errors


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


class DataFileWriter:
    """A class for writing sensor data to a CSV file.

    This class is a singleton. Every time a new file needs to be written this instance
    is reused.
    """

    def __init__(self) -> None:
        """Create a new DataFileWriter."""
        self._writer: Writer
        """The CSV writer."""

        # Listen to open/close messages
        pub.subscribe(self.open, "data_file.open")
        pub.subscribe(self.close, "data_file.close")

    @pubsub_errors("data_file.error")
    def open(self, path: Path) -> None:
        """Open a file at the specified path for writing.

        Args:
            path: The path of the file to write to
        """
        self._writer = Writer(path, _get_metadata(path.name))

        # Write column headers
        self._writer.writerow(
            (
                "Date",
                "Time",
                *(f"Temp{i+1}" for i in range(config.NUM_TEMPERATURE_MONITOR_CHANNELS)),
                "TimeAsSeconds",
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
        self._writer.close()

    @pubsub_errors("data_file.error")
    def write(self, time: datetime, temperatures: list[Decimal]) -> None:
        """Write temperature readings to the CSV file."""
        # Also include timestamp as seconds since midnight
        midnight = datetime(time.year, time.month, time.day)
        secs_since_midnight = floor((time - midnight).total_seconds())

        # TODO: Also write current angle and power to temperature controller
        self._writer.writerow(
            (
                time.strftime("%Y%m%d"),
                time.strftime("%H:%M:%S"),
                *temperatures,
                secs_since_midnight,
            )
        )


_data_file_writer = DataFileWriter()
"""The only instance of DataFileWriter."""
