"""Provides an enum representing the EM27's state."""
from dataclasses import dataclass
from decimal import Decimal
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


@dataclass
class EM27Property:
    """Class for representing EM27 monitored properties.

    Args:
        name: name of the physical quantity
        value: value of the physical quantity
        unit: unit in which the value is presented
    """

    name: str
    value: Decimal
    unit: str

    def __str__(self) -> str:
        """Print a property's name, value and unit in a readable format.

        Returns:
            str: The name, value and unit of a property.
        """
        return f"{self.name} = {self.value:.6f} {self.unit}"

    def val_str(self) -> str:
        """Print a property's value and unit in required format.

        Returns:
            str: The value and unit of a property in the format consistent with
                 the previous FINESSE GUI.
        """
        return f"{self.value:.6f} {self.unit}"
