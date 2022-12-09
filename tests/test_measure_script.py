"""Tests for the measure script code."""
import pytest

from finesse.gui.measure_script.parse import ParseError, parse_script


def test_valid_script() -> None:
    """Check that a valid measure script parses correctly."""
    txt = """
    count: 100
    sequence:
      - angle: nadir
        count: 1
      - angle: 4.0
        count: 1
    """

    script = parse_script(txt)
    assert script["count"] == 100
    seq = script["sequence"]
    assert len(seq) == 2
    assert seq[0] == {"angle": "nadir", "count": 1}
    assert seq[1] == {"angle": 4.0, "count": 1}


def test_invalid_scripts() -> None:
    """Check that various incorrectly formatted scripts raise a ParseError."""
    # count == 0
    with pytest.raises(ParseError):
        parse_script(
            """
            count: 0
            sequence:
              - angle: nadir
                count: 1
              - angle: 4.0
                count: 1
            """
        )

    # count == -1
    with pytest.raises(ParseError):
        parse_script(
            """
            count: -1
            sequence:
              - angle: nadir
                count: 1
              - angle: 4.0
                count: 1
            """
        )

    # Extra attribute
    with pytest.raises(ParseError):
        parse_script(
            """
            count: 100
            sequence:
              - angle: nadir
                count: 1
              - angle: 4.0
                count: 1
            extra_attribute: hello
            """
        )

    # Invalid preset
    with pytest.raises(ParseError):
        parse_script(
            """
            count: 100
            sequence:
              - angle: made_up_preset
                count: 1
              - angle: 4.0
                count: 1
            """
        )
