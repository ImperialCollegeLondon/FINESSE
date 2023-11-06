"""Provides a decorator for catching and forwarding errors via pubsub."""
import logging
import traceback
from collections.abc import Callable
from typing import Any

from decorator import decorator
from pubsub import pub


def _error_occurred(error_topic: str, error: BaseException) -> None:
    """Signal that an error occurred."""
    traceback_str = "".join(traceback.format_tb(error.__traceback__))

    # Write details including stack trace to program log
    logging.error(f"Caught error ({error_topic}): {str(error)}\n\n{traceback_str}")

    # Notify listeners
    pub.sendMessage(error_topic, error=error)


def pubsub_errors(error_topic: str, **extra_kwargs: Any) -> Callable:
    """Catch exceptions and broadcast via pubsub.

    Args:
        error_topic: The topic name on which to broadcast errors
    """

    def wrapped(func: Callable, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as error:
            _error_occurred(error_topic, error, **extra_kwargs)

    return decorator(wrapped)
