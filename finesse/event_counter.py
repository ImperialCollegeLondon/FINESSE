"""Provides a class for monitoring events such as device opening/closing."""
from collections.abc import Callable
from typing import Any

from pubsub import pub


class EventCounter:
    """A class for monitoring events such as device opening/closing.

    Callbacks are run when the desired count is reached and when the count drops below
    the target.
    """

    def __init__(
        self,
        target_count: int,
        on_target_reached: Callable[[], Any],
        on_below_target: Callable[[], Any],
    ) -> None:
        """Create a new EventCounter.

        Args:
            target_count: The target count on which on_target_reached will be run
            on_target_reached: Callback for when target_count is reached
            on_below_target: Callback for when count drops below target_count
        """
        self._count = 0
        self._target_count = target_count
        self._on_target_reached = on_target_reached
        self._on_below_target = on_below_target

    def increment(self) -> None:
        """Increase the counter by one and run callback if target reached."""
        self._count += 1
        if self._count == self._target_count:
            self._on_target_reached()

    def decrement(self) -> None:
        """Decrease the counter by one and run callback if count drops below target."""
        self._count -= 1
        if self._count == self._target_count - 1:
            self._on_below_target()

    def change_on_device_open(self, *names: str) -> None:
        """Subscribe to devices' open/close messages."""
        for name in names:
            pub.subscribe(self.increment, f"serial.{name}.opened")
            pub.subscribe(self.decrement, f"serial.{name}.close")
