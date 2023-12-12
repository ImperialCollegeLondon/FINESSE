"""Provides a base class for interfacing with the OPUS program."""
from __future__ import annotations

from abc import abstractmethod

from finesse.config import OPUS_TOPIC
from finesse.em27_info import EM27Status
from finesse.hardware.device import Device


class OPUSError(Exception):
    """Indicates that an error occurred with an OPUS device."""

    @classmethod
    def from_response(cls, errcode: int, errtext: str) -> OPUSError:
        """Create an OPUSError from the information given in the device response."""
        return cls(f"Error {errcode}: {errtext}")


class OPUSInterfaceBase(Device, name=OPUS_TOPIC, description="OPUS device"):
    """Base class providing an interface to the OPUS program."""

    def __init__(self) -> None:
        """Create a new OPUSInterfaceBase."""
        super().__init__()
        self.subscribe(self.request_command, "request")

    @abstractmethod
    def request_command(self, command: str) -> None:
        """Request that OPUS run the specified command.

        Note that we treat "status" as a command, even though it requires a different
        URL to access.

        Args:
            command: Name of command to run
        """

    def send_response(self, command: str, status: EM27Status, text: str) -> None:
        """Broadcast the device's response via pubsub."""
        self.send_message(f"response.{command}", status=status, text=text)
