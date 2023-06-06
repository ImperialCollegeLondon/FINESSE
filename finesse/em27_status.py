"""Provides an enum representing the EM27's state."""
from enum import Enum


class EM27Status(Enum):
    """The state of the EM27 interferometer.

    These values are taken from the manual.
    """

    IDLE = 0
    CONNECTING = 1
    CONNECTED = 2
    MEASURING = 3
    FINISHING = 4
    CANCELLING = 5
    UNDEFINED = 6

    @property
    def is_connected(self) -> bool:
        """Whether the state represents a connected status."""
        return 2 <= self.value <= 5
