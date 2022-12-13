"""Tests for the interface to the TC4820 device."""
from contextlib import nullcontext as does_not_raise
from itertools import chain
from typing import Any, Tuple

import pytest
from pytest_mock import MockerFixture

from finesse.hardware.tc4820 import TC4820, MalformedMessageError


@pytest.fixture
def dev(mocker: MockerFixture) -> TC4820:
    """Get an instance of a TC4820 object."""
    serial = mocker.patch("serial.Serial")
    tc_dev = TC4820(serial)

    # Check default argument
    assert tc_dev.max_retries == 3
    return tc_dev


def checksum(message: int) -> int:
    """Calculate the checksum as an int."""
    return sum(f"{message:0{4}x}".encode("ascii")) & 0xFF


def format_message(message: int, checksum: int) -> bytes:
    """Format the message as the device would."""
    assert 0 <= checksum <= 0xFF
    return f"*{message:0{4}x}{checksum:0{2}x}^".encode("ascii")


_MESSAGE = "012345678"


def _get_message(len: int) -> Tuple[int, bytes, Any]:
    substr = _MESSAGE[:len]
    value = int(substr, base=16)
    return (
        value,
        f"*{substr}{checksum(value):0{2}x}^".encode("ascii"),
        does_not_raise() if len == 4 else pytest.raises(MalformedMessageError),
    )


@pytest.mark.parametrize(
    "value,message,raises",
    chain(
        # This is a special message indicating that we provided a bad checksum to the
        # device
        [(0, b"*XXXX60^", pytest.raises(MalformedMessageError))],
        # Non-hex value for number
        [(0, b"*$$$$90^", pytest.raises(MalformedMessageError))],
        # Message length
        [_get_message(len) for len in range(1, len(_MESSAGE))],
        # Test checksums
        [
            (
                value,
                format_message(value, csum),
                does_not_raise()
                if checksum(value) == csum
                else pytest.raises(MalformedMessageError),
            )
            for value in (0x0000, 0x1234, 0x5678)
            for csum in range(0x100)
        ],
    ),
)
def test_read(
    value: int, message: bytes, raises: Any, dev: TC4820, mocker: MockerFixture
) -> None:
    """Test inputs to TC4820.read()."""
    with raises:
        m = mocker.patch("serial.Serial.read_until", return_value=message)
        assert value == dev.read()
        m.assert_called_once_with(b"^", size=8)
