"""Tests for the measure script code."""
from contextlib import nullcontext as does_not_raise
from typing import Any, Dict

import pytest
import yaml

from finesse.config import ANGLE_PRESETS
from finesse.gui.measure_script.parse import ParseError, parse_script


def is_valid_angle(angle: Any) -> bool:
    """Check whether the angle is valid."""
    if isinstance(angle, float):
        # TODO: We should probably check that the angle is within valid range too
        return True

    if angle in ANGLE_PRESETS:
        return True

    return False


def get_data(count: int, angle: Any, num_attributes: int) -> Dict[str, Any]:
    """Get all or part of data script."""
    data = {
        "count": count,
        "sequence": [
            {"angle": angle, "count": 1},
            {"angle": 4.0, "count": 1},
        ],
        "extra_attribute": "hello",
    }

    return {k: data[k] for k in list(data.keys())[:num_attributes]}


@pytest.mark.parametrize(
    "data,raises",
    [
        (
            get_data(count, angle, num_attributes),
            does_not_raise()
            if count > 0 and is_valid_angle(angle) and num_attributes == 2
            else pytest.raises(ParseError),
        )
        for count in range(-5, 5)
        for angle in (4.0, 4, "nadir", "NADIR", "badger", "kevin", "")
        for num_attributes in range(3)
    ],
)
def test_parse_script(data: Dict[str, Any], raises: Any) -> None:
    """Check that errors are thrown for invalid data.

    Note that we don't check that serialisation and deserialisation work correctly as it
    is assumed that PyYAML is doing this correctly.
    """
    with raises:
        parse_script(yaml.safe_dump(data))
