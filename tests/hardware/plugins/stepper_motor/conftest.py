"""Fixtures for stepper motor tests."""
from unittest.mock import MagicMock

import pytest
from decorator import decorator

from finesse.hardware.plugins.stepper_motor import stepper_motor_base


def null_decorator(*args, **kwargs):
    """A decorator which simply returns the provided function."""

    def wrapped(func, *args, **kwargs):
        return func(*args, **kwargs)

    return decorator(wrapped)


@pytest.fixture
def error_wrap_mock(monkeypatch) -> MagicMock:
    """Mock the error_wrap decorator to avoid decorator errors."""
    mock = MagicMock()
    monkeypatch.setattr(stepper_motor_base, "error_wrap", mock)
    return mock
