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
    logging.error(f"Caught error ({error_topic}): {error!s}\n\n{traceback_str}")

    # Notify listeners
    pub.sendMessage(error_topic, error=error)


@decorator
def pubsub_errors(func: Callable, self: Any, *args, **kwargs):
    """Catch exceptions and broadcast via pubsub.

    Args:
        func: The function to decorate
        self: The object providing the error_topic member
        args: Arguments for func
        kwargs: Keyword arguments for func
    """
    try:
        return func(self, *args, **kwargs)
    except Exception as error:
        _error_occurred(self.error_topic, error)
