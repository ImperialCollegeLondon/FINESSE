"""Provides a base class for interfacing with the OPUS program."""
from __future__ import annotations

from abc import abstractmethod

from finesse.config import SPECTROMETER_TOPIC
from finesse.hardware.device import Device
from finesse.spectrometer_status import SpectrometerStatus


class OPUSError(Exception):
    """Indicates that an error occurred with an OPUS device."""

    @classmethod
    def from_response(cls, errcode: int, errtext: str) -> OPUSError:
        """Create an OPUSError from the information given in the device response."""
        return cls(f"Error {errcode}: {errtext}")


class OPUSInterfaceBase(Device, name=SPECTROMETER_TOPIC, description="OPUS device"):
    """Base class providing an interface to the OPUS program."""

    def __init__(self) -> None:
        """Create a new OPUSInterfaceBase."""
        super().__init__()
        self.subscribe(self.request_command, "request")

    @abstractmethod
    def request_command(self, command: str) -> None:
        """Request that OPUS run the specified command.

        Args:
            command: Name of command to run
        """

    def send_status_message(self, status: SpectrometerStatus) -> None:
        """Send a status update via pubsub."""
        self.send_message(f"status.{status.name.lower()}", status=status)
