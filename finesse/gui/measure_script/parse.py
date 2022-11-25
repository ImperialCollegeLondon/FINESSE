"""Code for parsing the YAML-formatted measure scripts."""
import logging
from dataclasses import dataclass
from io import TextIOBase
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from pubsub import pub
from PySide6.QtWidgets import QWidget
from schema import And, Or, Schema, SchemaError

from ...config import ANGLE_PRESETS
from ..error_message import show_error_message


def _take_measurements(count: int, angle: Union[str, float]) -> None:
    """A placeholder function for recording multiple measurements."""
    # Move the mirror to the correct location
    pub.sendMessage("stepper.move", target=angle)

    # Take the recordings
    logging.info(f"Recording {count} measurements")


@dataclass
class Script:
    """Represents a measure script, including its file path and data."""

    path: Path
    measurements: Dict[str, Any]

    def run(self) -> None:
        """Run this measure script."""
        logging.info(f"Running {self.path}")
        for i in range(self.measurements["count"]):
            logging.info(f"Iteration {i+1}/{self.measurements['count']}")
            for instruction in self.measurements["sequence"]:
                _take_measurements(instruction["count"], instruction["angle"])


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
            return Script(file_path, parse_script(f))
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
    valid_preset = And(str, lambda s: s in ANGLE_PRESETS)
    count_type = And(int, lambda x: x > 0)
    schema = Schema(
        {
            "measurements": {
                "count": count_type,
                "sequence": [{"angle": Or(float, valid_preset), "count": count_type}],
            }
        }
    )

    try:
        return schema.validate(yaml.safe_load(script))["measurements"]
    except (yaml.YAMLError, SchemaError) as e:
        raise ParseError() from e
