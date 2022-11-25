"""Code for parsing the YAML-formatted measure scripts."""
from io import TextIOBase
from typing import Any, Dict, Union

import yaml
from schema import And, Or, Schema, SchemaError

from ...config import ANGLE_PRESETS


class ParseError(Exception):
    """An error occurred while parsing a measure script."""

    def __init__(_) -> None:
        """Create a new ParseError."""
        super().__init__("Error parsing measure script")


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
