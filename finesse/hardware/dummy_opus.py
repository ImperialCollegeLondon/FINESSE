"""Provides a dummy EM27 device for interfacing with."""

import logging
from enum import Enum
from typing import Optional

from pubsub import pub
from PySide6.QtCore import QTimer, Signal, Slot
from statemachine import State, StateMachine
from statemachine.exceptions import TransitionNotAllowed

from .opus_interface_base import OPUSInterfaceBase


class OPUSError(Enum):
    """Represents an error code and description for OPUS errors.

    The codes and descriptions are taken from the manual.
    """

    NO_ERROR = (0, "No error")
    NOT_IDLE = (1, "Status is not 'Idle' although required for current command")
    NOT_RUNNING = (2, "Status is not 'Running' although required for current command")
    NOT_RUNNING_OR_FINISHING = (
        3,
        "Status is not 'Running' or 'Finishing' although required for current command",
    )
    UNKNOWN_COMMAND = (4, "Unknown command")
    WEBSITE_NOT_FOUND = (5, "Website not found")
    NO_RESULT = (6, "No result available")
    NOT_CONNECTED = (7, "System not connected")

    def to_tuple(self) -> Optional[tuple[int, str]]:
        """Convert to a (code, message) tuple or None if no error."""
        if self == OPUSError.NO_ERROR:
            return None
        return self.value


class OPUSStateMachine(StateMachine):
    """An FSM for keeping track of the internal state of the mock device."""

    idle = State("Idle", 0, initial=True)
    connecting = State("Connecting", 1)
    connected = State("Connected", 2)
    measuring = State("Measuring", 3)
    finishing = State("Finishing current measurement", 4)
    cancelling = State("Cancelling", 5)
    # The manual also describes an "Undefined" state, which we aren't using

    _start_connecting = idle.to(connecting)
    _finish_connecting = connecting.to(connected)

    start_measuring = connected.to(measuring)
    _start_finishing_measuring = measuring.to(finishing)
    _finish_measuring = finishing.to(connected)
    _cancel_measuring = measuring.to(cancelling)
    _reset_after_cancelling = cancelling.to(connected)

    def connect(self) -> None:
        """Connect to the device."""
        self._start_connecting()
        self._finish_connecting()

    def cancel(self) -> None:
        """Cancel the current measurement."""
        self._cancel_measuring()
        self._reset_after_cancelling()
        logging.info("Cancelling current measurement")

    def stop(self) -> None:
        """Finish measurement successfully."""
        self._start_finishing_measuring()
        self._finish_measuring()

    def on_enter_state(self, target: State) -> None:
        """Log all state transitions."""
        logging.info(f"Current state: {target.name}")


class DummyOPUSInterface(OPUSInterfaceBase):
    """A mock version of the OPUS API for testing purposes."""

    _request_status = Signal()
    _request_command = Signal(str)

    def __init__(self, measure_duration: float = 1.0) -> None:
        """Create a new DummyOPUSInterface.

        Args:
            measure_duration: How long a single measurement takes (seconds)
        """
        super().__init__()

        self.last_error = OPUSError.NO_ERROR
        """The last error which occurred."""
        self.state_machine = OPUSStateMachine()
        """An object representing the internal state of the device."""

        self.measure_timer = QTimer(self)
        """Timer signalling the end of a measurement."""
        self.measure_timer.setInterval(round(measure_duration * 1000))
        self.measure_timer.setSingleShot(True)
        self.measure_timer.timeout.connect(self.finish_measuring)  # type: ignore

    def __del__(self) -> None:
        """Stop the background timer."""
        self.measure_timer.stop()

    def _send_response(self, type: str) -> None:
        """Send a message signalling that a response was received."""
        state = self.state_machine.current_state

        pub.sendMessage(
            f"opus.{type}.response",
            url="https://example.com",
            status=state.value,
            text=state.name,
            error=self.last_error.to_tuple(),
        )

    def request_status(self) -> None:
        """Request the device's current status."""
        if self.state_machine.current_state == OPUSStateMachine.idle:
            self.last_error = OPUSError.NOT_CONNECTED

        self._send_response("status")

    def request_command(self, command: str) -> None:
        """Execute the specified command on the device."""
        self.last_error = OPUSError.NO_ERROR

        if command == "cancel":
            try:
                self.state_machine.cancel()
                self.measure_timer.stop()
            except TransitionNotAllowed:
                self.last_error = OPUSError.NOT_RUNNING
        elif command == "stop":
            try:
                self.state_machine.stop()
                self.measure_timer.stop()
            except TransitionNotAllowed:
                # TODO: This currently won't work if it actually *is* finishing
                self.last_error = OPUSError.NOT_RUNNING_OR_FINISHING
        elif command == "start":
            try:
                self.state_machine.start_measuring()
                self.measure_timer.start()
            except TransitionNotAllowed:
                self.last_error = OPUSError.NOT_CONNECTED
        elif command == "connect":
            try:
                self.state_machine.connect()
            except TransitionNotAllowed:
                self.last_error = OPUSError.NOT_IDLE
        else:
            self.last_error = OPUSError.UNKNOWN_COMMAND

        self._send_response("command")

    @Slot()
    def finish_measuring(self) -> None:
        """Finish measurement successfully."""
        self.last_error = OPUSError.NO_ERROR

        self.state_machine.stop()
        logging.info("Measurement complete")
