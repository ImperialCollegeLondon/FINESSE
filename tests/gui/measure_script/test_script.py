"""Tests for the measure script code."""
from contextlib import nullcontext as does_not_raise
from itertools import chain
from pathlib import Path
from typing import Any, Dict, Union
from unittest.mock import patch

import pytest
import yaml
from PySide6.QtWidgets import QWidget

from finesse.config import ANGLE_PRESETS
from finesse.gui.measure_script.script import (
    Measurement,
    ParseError,
    Script,
    parse_script,
)


def is_valid_angle(angle: Any) -> bool:
    """Check whether the angle is valid."""
    if isinstance(angle, float) and 0.0 <= angle < 360.0:
        return True

    if angle in ANGLE_PRESETS:
        return True

    return False


def get_data(repeats: int, angle: Any, num_attributes: int) -> Dict[str, Any]:
    """Get all or part of data script.

    Passing angle==() allows for testing with an empty sequence.
    """
    if angle == ():
        angles = []
    else:
        angles = [
            {"angle": angle, "measurements": 1},
            {"angle": 4.0, "measurements": 1},
        ]
    data = {
        "repeats": repeats,
        "sequence": angles,
        "extra_attribute": "hello",
    }

    return {k: data[k] for k in list(data.keys())[:num_attributes]}


@pytest.mark.parametrize(
    "data,raises",
    [
        (
            get_data(repeats, angle, num_attributes),
            does_not_raise()
            if repeats > 0 and is_valid_angle(angle) and num_attributes == 2
            else pytest.raises(ParseError),
        )
        for repeats in range(-5, 5)
        for angle in chain(
            (float(i) for i in range(-180, 541, 60)),
            (4, "nadir", "NADIR", "badger", "kevin", "", ()),
        )
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


@pytest.mark.parametrize("angle", ("nadir", 90.0))
def test_measurement_to_dict(angle: Union[str, float]) -> None:
    """Check Measurement's to_dict() method."""
    d = Measurement(angle, 5)
    assert d.to_dict() == {"angle": angle, "measurements": 5}


_SCRIPT_PATH = Path(__file__).parent / "test_script.yaml"


def test_try_load_success(qtbot) -> None:
    """Test the try_load() function."""
    script = Script.try_load(QWidget(), _SCRIPT_PATH)
    assert script, "Script could not be loaded"

    assert script.repeats == 1
    assert len(script.sequence) == 2
    assert script.sequence[0] == Measurement("zenith", 1)
    assert script.sequence[1] == Measurement(0.0, 1)


@pytest.mark.parametrize(
    "exception,raises",
    (
        (OSError(), does_not_raise()),
        (ParseError(), does_not_raise()),
        (Exception(), pytest.raises(Exception)),
    ),
)
@patch("finesse.gui.measure_script.script.show_error_message")
def test_try_load_fail(
    show_error_mock: Any, exception: BaseException, raises: Any, qtbot
) -> None:
    """Test the try_load() function."""
    with patch("finesse.gui.measure_script.script.parse_script", side_effect=exception):
        with raises:
            script = Script.try_load(QWidget(), _SCRIPT_PATH)
            assert script is None, "Script should not have been loaded"
            show_error_mock.assert_called_once()
