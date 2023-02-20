"""Code for parsing the YAML-formatted measure scripts."""
import logging
from dataclasses import dataclass
from io import TextIOBase
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Union

import yaml
from pubsub import pub
from PySide6.QtWidgets import QWidget
from schema import And, Or, Schema, SchemaError

from ...config import ANGLE_PRESETS
from ..error_message import show_error_message


@dataclass
class Measurement:
    """Represents a single step (i.e. angle + number of measurements)."""

    angle: Union[str, float]
    """Either an angle in degrees or the name of a preset angle."""

    measurements: int
    """The number of times to record a measurement at this position."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert this object to a dict."""
        return {"angle": self.angle, "measurements": self.measurements}

    def run(self) -> None:
        """A placeholder function for recording multiple measurements."""
        # Move the mirror to the correct location
        pub.sendMessage("stepper.move.begin", target=self.angle)

        # Take the recordings
        logging.info(f"Recording {self.measurements} measurements")


class Script:
    """Represents a measure script, including its file path and data."""

    def __init__(
        self, path: Path, repeats: int, sequence: Sequence[Dict[str, Any]]
    ) -> None:
        """Create a new Script.

        Args:
            path: The file path to this measure script
            repeats: The number of times to repeat the sequence of measurements
            sequence: Different measurements (i.e. angle + num measurements) to record
        """
        self.path = path
        self.repeats = repeats
        self.sequence = [Measurement(**val) for val in sequence]

    def run(self) -> None:
        """Run this measure script."""
        logging.info(f"Running {self.path}")
        for i in range(self.repeats):
            logging.info(f"Iteration {i+1}/{self.repeats}")
            for instruction in self.sequence:
                instruction.run()


class ParseError(Exception):
    """An error occurred while parsing a measure script."""

    def __init__(_) -> None:
        """Create a new ParseError."""
        super().__init__("Error parsing measure script")


def try_load_script(parent: QWidget, file_path: Path) -> Optional[Script]:
    """Try to load a measure script at the specified path.

    Args:
        parent: The parent widget (for error messages shown)
        file_path: The path to the script to be loaded
    Returns:
        A Script if successful, else None
    """
    try:
        with open(file_path, "r") as f:
            return Script(file_path, **parse_script(f))
    except OSError as e:
        show_error_message(parent, f"Error: Could not read {file_path}: {str(e)}")
    except ParseError:
        show_error_message(parent, f"Error: {file_path} is in an invalid format")
    return None


def parse_script(script: Union[str, TextIOBase]) -> Dict[str, Any]:
    """Parse a measure script.

    Args:
        script: The contents of the script as YAML or a stream containing YAML
    Raises:
        ParseError: The script's contents were invalid
    """
    valid_float = And(float, lambda f: 0.0 <= f < 360.0)
    valid_preset = And(str, lambda s: s in ANGLE_PRESETS)
    measurements_type = And(int, lambda x: x > 0)
    nonempty_list = And(list, lambda x: x)

    schema = Schema(
        {
            "repeats": measurements_type,
            "sequence": And(
                nonempty_list,
                [
                    {
                        "angle": Or(valid_float, valid_preset),
                        "measurements": measurements_type,
                    }
                ],
            ),
        }
    )

    try:
        return schema.validate(yaml.safe_load(script))
    except (yaml.YAMLError, SchemaError) as e:
        raise ParseError() from e
