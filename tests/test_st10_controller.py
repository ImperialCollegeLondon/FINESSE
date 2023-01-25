"""Tests for the ST10Controller class."""
from contextlib import nullcontext as does_not_raise
from itertools import chain
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from serial import SerialTimeoutException

from finesse.hardware.st10_controller import ST10Controller, ST10ControllerError


@pytest.fixture
def dev() -> ST10Controller:
    """A fixture providing an ST10Controller with a patched Serial object."""
    serial = MagicMock()

    # check_device_id() and home() should both be called by ST10Controller.__init__(),
    # but patch them for now as we'll test their inner workings elsewhere
    with patch.object(ST10Controller, "_check_device_id"):
        with patch.object(ST10Controller, "home"):
            return ST10Controller(serial)


def read_mock(dev: ST10Controller, return_value: str):
    """Patch the _read() method of dev."""
    return patch.object(dev, "_read", return_value=return_value)


def test_write(dev: ST10Controller) -> None:
    """Test the _write() method."""
    dev._write("hello")
    dev.serial.write.assert_called_once_with(b"hello\r")


def test_init() -> None:
    """Test __init__()."""
    serial = MagicMock()

    with patch.object(ST10Controller, "_check_device_id") as check_mock:
        with patch.object(ST10Controller, "home") as home_mock:
            ST10Controller(serial)
            check_mock.assert_called_once()
            home_mock.assert_called_once()


def test_read(dev: ST10Controller) -> None:
    """Test the _read() method."""
    # Check a normal read
    dev.serial.read_until.return_value = b"hello\r"
    ret = dev._read()
    dev.serial.read_until.assert_called_with(b"\r")
    assert ret == "hello"

    # Check a timed-out read
    dev.serial.read_until.return_value = b""
    with pytest.raises(SerialTimeoutException):
        dev._read()

    # Check a non-ASCII return value
    dev.serial.read_until.return_value = b"\xff\r"
    with pytest.raises(ST10ControllerError):
        dev._read()


@pytest.mark.parametrize(
    "response,raises",
    [
        (
            response,
            does_not_raise()
            if response in ("%", "*")
            else pytest.raises(ST10ControllerError),
        )
        for response in ["%", "*", "?error", "something else"]
    ],
)
def test_check_response(response: str, raises: Any, dev: ST10Controller) -> None:
    """Test the _check_response() method."""
    with read_mock(dev, response):
        with raises:
            dev._check_response()


def test_write_check(dev: ST10Controller) -> None:
    """Test the _write_check() method."""
    with patch.object(dev, "_write") as write_mock:
        with patch.object(dev, "_check_response") as check_mock:
            dev._write_check("hello")
            write_mock.assert_called_once_with("hello")
            check_mock.assert_called_once()


@pytest.mark.parametrize(
    "name,value,response,raises",
    [
        (
            name,
            value,
            response,
            does_not_raise()
            if response.startswith(f"{name}=")
            else pytest.raises(ST10ControllerError),
        )
        for name in ["hello", "IS", "SP"]
        for value in ["", "value", "123"]
        for response in [f"{name}={value}", value, "%", "*", "?4"]
    ],
)
def test_request_value(
    name: str, value: str, response: str, raises: Any, dev: ST10Controller
) -> None:
    """Test the _request_value() method."""
    with patch.object(dev, "_write") as write_mock:
        with read_mock(dev, response):
            with raises:
                assert dev._request_value(name) == value
            write_mock.assert_called_once_with(name)


def test_check_device_id(dev: ST10Controller) -> None:
    """Test the _check_device_id() method."""
    # Check with the correct ID
    with read_mock(dev, "107F024"):
        dev._check_device_id()

    # Check with an invalid ID
    with read_mock(dev, "hello"):
        with pytest.raises(ST10ControllerError):
            dev._check_device_id()


@pytest.mark.parametrize(
    "step,response,raises",
    chain(
        [(step, f"SP={step}", does_not_raise()) for step in range(0, 250, 50)],
        [(4, "SP=hello", pytest.raises(ST10ControllerError))],
    ),
)
def test_get_step(step: int, response: str, raises: Any, dev: ST10Controller) -> None:
    """Test getting the step property."""
    with read_mock(dev, response):
        with raises:
            assert dev.step == step
