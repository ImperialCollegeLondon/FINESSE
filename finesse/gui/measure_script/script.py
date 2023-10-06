"""An interface for using the YAML-formatted measure scripts.

This includes code for parsing and running the scripts.
"""
from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from io import TextIOBase
from pathlib import Path
from typing import Any

import yaml
from pubsub import pub
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget
from schema import And, Or, Schema, SchemaError
from statemachine import State, StateMachine

from ...config import ANGLE_PRESETS, STEPPER_MOTOR_TOPIC
from ...em27_status import EM27Status
from ..error_message import show_error_message


@dataclass(frozen=True)
class Measurement:
    """Represents a single step (i.e. angle + number of measurements)."""

    angle: float | str
    """Either an angle in degrees or the name of a preset angle."""

    measurements: int
    """The number of times to record a measurement at this position."""


class Script:
    """Represents a measure script, including its file path and data."""

    def __init__(
        self, path: Path, repeats: int, sequence: Sequence[dict[str, Any]]
    ) -> None:
        """Create a new Script.

        Args:
            path: The file path to this measure script
            repeats: The number of times to repeat the sequence of measurements
            sequence: Different measurements (i.e. angle + num measurements) to record
        """
        self.path = path
        self.repeats = repeats
        self.sequence = [Measurement(**val) for val in sequence]
        self.runner: ScriptRunner | None = None

    def __iter__(self) -> ScriptIterator:
        """Get an iterator for the measurements."""
        return ScriptIterator(self)

    def run(self, parent: QWidget | None = None) -> None:
        """Run this measure script."""
        logging.info(f"Running {self.path}")
        self.runner = ScriptRunner(self, parent=parent)
        self.runner.start_moving()

    @classmethod
    def try_load(cls, parent: QWidget, file_path: Path) -> Script | None:
        """Try to load a measure script at the specified path.

        Args:
            parent: The parent widget (for error messages shown)
            file_path: The path to the script to be loaded
        Returns:
            A Script if successful, else None
        """
        try:
            with open(file_path) as f:
                return cls(file_path, **parse_script(f))
        except OSError as e:
            show_error_message(parent, f"Error: Could not read {file_path}: {str(e)}")
        except ParseError:
            show_error_message(parent, f"Error: {file_path} is in an invalid format")
        return None


class ParseError(Exception):
    """An error occurred while parsing a measure script."""

    def __init__(_) -> None:
        """Create a new ParseError."""
        super().__init__("Error parsing measure script")


def parse_script(script: str | TextIOBase) -> dict[str, Any]:
    """Parse a measure script.

    Args:
        script: The contents of the script as YAML or a stream containing YAML
    Raises:
        ParseError: The script's contents were invalid
    """
    valid_float = And(float, lambda f: 0.0 <= f < 360.0)
    valid_preset = And(str, lambda s: s in ANGLE_PRESETS)
    measurements_type = And(int, lambda x: x > 0)
    nonempty_list = And(list, lambda x: x)

    schema = Schema(
        {
            "repeats": measurements_type,
            "sequence": And(
                nonempty_list,
                [
                    {
                        "angle": Or(valid_float, valid_preset),
                        "measurements": measurements_type,
                    }
                ],
            ),
        }
    )

    try:
        return schema.validate(yaml.safe_load(script))
    except (yaml.YAMLError, SchemaError) as e:
        raise ParseError() from e


def _poll_em27_status() -> None:
    """Request the EM27's status from OPUS."""
    pub.sendMessage("opus.request", command="status")


class ScriptIterator:
    """Allows for iterating through a Script with the required number of repeats."""

    def __init__(self, script: Script) -> None:
        """Create a new ScriptIterator.

        Args:
            script: The Script from which to create this iterator.
        """
        self._sequence_iter = iter(script.sequence)
        self.script = script
        self.current_repeat = 0

    def __iter__(self) -> ScriptIterator:
        """Return self."""
        return self

    def __next__(self) -> Measurement:
        """Return the next Measurement in the sequence."""
        try:
            return next(self._sequence_iter)
        except StopIteration:
            self.current_repeat = min(self.script.repeats, self.current_repeat + 1)
            if self.current_repeat == self.script.repeats:
                raise

            self._sequence_iter = iter(self.script.sequence)
            return next(self)


class ScriptRunner(StateMachine):
    """A class for running measure scripts.

    The ScriptRunner is a finite state machine. Besides the one initial state, the
    runner can either be in a "moving" state (i.e. the motor is moving) or a "measuring"
    state (i.e. the motor is stationary and the EM27 is recording a measurement).

    The state diagram looks like this:

    ![](../../../../script_runner_graph.png)
    """

    not_running = State("Not running", initial=True)
    """State indicating that the script is not yet running or has finished."""
    waiting_to_move = State("Waiting to move")
    """State indicating that the motor will move when the script is unpaused."""
    moving = State("Moving")
    """State indicating that the motor is moving."""
    waiting_to_measure = State("Waiting to measure")
    """State indicating that measurement will start when the script is unpaused."""
    measuring = State("Measuring")
    """State indicating that a measurement is taking place."""

    start_moving = not_running.to(moving)
    """Start moving the motor to the required angle for the current measurement."""
    finish_waiting_for_move = waiting_to_move.to(moving)
    """Stop waiting and start the next move."""
    cancel_move = moving.to(
        not_running, after=lambda: pub.sendMessage(f"device.{STEPPER_MOTOR_TOPIC}.stop")
    )
    """Cancel the current movement."""
    start_measuring = moving.to(waiting_to_measure)
    """Start recording the current measurement."""
    repeat_measuring = measuring.to(waiting_to_measure)
    """Record another measurement at the same angle."""
    finish_waiting_for_measure = waiting_to_measure.to(measuring)
    """Stop waiting and start the next measurement."""
    cancel_measuring = measuring.to(not_running)
    """Cancel the current measurement."""
    start_next_move = measuring.to(waiting_to_move)
    """Trigger a move to the angle for the next measurement."""
    finish = moving.to(not_running)
    """To be called when all measurements are complete."""

    def __init__(
        self,
        script: Script,
        min_poll_interval: float = 1.0,
        parent: QWidget | None = None,
    ) -> None:
        """Create a new ScriptRunner.

        Note that the EM27 often takes more than one second to respond to requests,
        hence why we set a minimum polling interval rather than an absolute one.

        Args:
            script: The script to run
            min_poll_interval: Minimum rate at which to poll EM27 (seconds)
            parent: The parent widget

        Todo:
            Error handling for the stepper motor
        """
        self.script = script
        """The running script."""
        self.measurement_iter = iter(self.script)
        """An iterator yielding the required sequence of measurements."""
        self.parent = parent
        """The parent widget."""
        self.paused = False
        """Whether the script is paused."""

        self.current_measurement: Measurement
        """The current measurement to acquire."""
        self.current_measurement_count: int
        """How many times a measurement has been recorded at the current angle."""

        self._check_status_timer = QTimer()
        """A timer which checks whether the EM27's measurement is complete."""
        self._check_status_timer.setSingleShot(True)
        self._check_status_timer.setInterval(round(1000 * min_poll_interval))
        self._check_status_timer.timeout.connect(_poll_em27_status)

        # Send stop command in case motor is moving
        pub.sendMessage(f"device.{STEPPER_MOTOR_TOPIC}.stop")

        # Actions to control the script
        pub.subscribe(self.abort, "measure_script.abort")
        pub.subscribe(self.pause, "measure_script.pause")
        pub.subscribe(self.unpause, "measure_script.unpause")

        super().__init__()

    def before_start_moving(self) -> None:
        """Send a pubsub message to indicate that the script is running."""
        pub.sendMessage("measure_script.begin", script_runner=self)

    def on_enter_state(self, target: State, event: str) -> None:
        """Log the state every time it changes."""
        logging.info(f"Measure script: Entering state {target.name} (event: {event})")

    def on_enter_not_running(self, event: str) -> None:
        """If finished, unsubscribe from pubsub messages and send message."""
        if event == "__initial__":
            # If this is the first state, do nothing
            return

        # Stepper motor messages
        pub.unsubscribe(self.start_measuring, f"device.{STEPPER_MOTOR_TOPIC}.move.end")
        pub.unsubscribe(
            self._on_stepper_motor_error, f"device.error.{STEPPER_MOTOR_TOPIC}"
        )

        # EM27 messages
        pub.unsubscribe(self._measuring_error, "opus.error")
        pub.unsubscribe(self._measuring_started, "opus.response.start")
        pub.unsubscribe(self._status_received, "opus.response.status")

        # Send message signalling that the measure script is no longer running
        pub.sendMessage("measure_script.end")

    def on_exit_not_running(self) -> None:
        """Subscribe to pubsub messages for the stepper motor and OPUS."""
        # Listen for stepper motor messages
        pub.subscribe(self.start_measuring, f"device.{STEPPER_MOTOR_TOPIC}.move.end")
        pub.subscribe(
            self._on_stepper_motor_error, f"device.error.{STEPPER_MOTOR_TOPIC}"
        )

        # Listen for EM27 messages
        pub.subscribe(self._measuring_error, "opus.error")
        pub.subscribe(self._measuring_started, "opus.response.start")
        pub.subscribe(self._status_received, "opus.response.status")

    def _load_next_measurement(self) -> bool:
        """Load the next measurement in the sequence.

        Returns:
            False if there are no more measurements
        """
        try:
            self.current_measurement = next(self.measurement_iter)
            self.current_measurement_count = 0
            return True
        except StopIteration:
            return False

    def on_enter_moving(self) -> None:
        """Try to load the next measurement and start the next movement.

        If there are no more measurements, the ScriptRunner will return to a not_running
        state.
        """
        if not self._load_next_measurement():
            self.finish()
            return

        pub.sendMessage("measure_script.start_moving", script_runner=self)

        # Start moving the stepper motor
        pub.sendMessage(
            f"device.{STEPPER_MOTOR_TOPIC}.move.begin",
            target=self.current_measurement.angle,
        )

        # Flag that we want a message when the movement has stopped
        pub.sendMessage(f"device.{STEPPER_MOTOR_TOPIC}.notify_on_stopped")

    def on_enter_measuring(self) -> None:
        """Tell the EM27 to start a new measurement.

        NB: This is also invoked on repeat measurements
        """
        pub.sendMessage("measure_script.start_measuring", script_runner=self)
        pub.sendMessage("opus.request", command="start")

    def on_exit_measuring(self) -> None:
        """Ensure that the polling timer is stopped."""
        self._check_status_timer.stop()

    def on_enter_waiting_to_move(self) -> None:
        """Move onto the next move unless the script is paused."""
        if not self.paused:
            self.finish_waiting_for_move()

    def on_enter_waiting_to_measure(self) -> None:
        """Move onto the next measurement unless the script is paused."""
        if not self.paused:
            self.finish_waiting_for_measure()

    def _measuring_started(
        self,
        status: EM27Status,
        text: str,
        error: tuple[int, str] | None,
    ):
        """Start polling the EM27 so we know when the measurement is finished."""
        if error:
            self._on_em27_error_message(*error)
        else:
            _poll_em27_status()

    def _status_received(
        self,
        status: EM27Status,
        text: str,
        error: tuple[int, str] | None,
    ):
        """Move on to the next measurement if the measurement has finished."""
        if error:
            self._on_em27_error_message(*error)
            return

        if status == EM27Status.CONNECTED:  # indicates measurement is finished
            self._measuring_end()
        else:
            # Poll again later
            self._check_status_timer.start()

    def abort(self) -> None:
        """Abort the current measure script run."""
        # For some reason mypy seems not to be able to deduce the type of current_state
        match self.current_state:  # type: ignore[has-type]
            case self.moving:
                self.cancel_move()
            case self.measuring:
                self.cancel_measuring()
            case self.waiting_to_measure | self.waiting_to_move:
                # These states don't need any special handling
                self.current_state = self.not_running

        logging.info("Aborting measure script")

    def pause(self) -> None:
        """Pause the current measure script run."""
        self.paused = True

    def unpause(self) -> None:
        """Unpause the current measure script run."""
        self.paused = False

        # Move onto the next step if needed
        match self.current_state:
            case self.waiting_to_move:
                self.finish_waiting_for_move()
            case self.waiting_to_measure:
                self.finish_waiting_for_measure()

    def _on_stepper_motor_error(self, error: BaseException) -> None:
        """Call abort()."""
        self.abort()

    def _on_em27_error(self, message: str) -> None:
        """Cancel current measurement and show an error message to the user."""
        self.abort()

        show_error_message(
            self.parent,
            f"EM27 error occurred. Measure script will stop running.\n\n{message}",
        )

    def _on_em27_error_message(self, errcode: int, errmsg: str) -> None:
        """Error reported by EM27 system."""
        self._on_em27_error(f"Error {errcode}: {errmsg}")

    def _measuring_error(self, error: BaseException) -> None:
        """Log errors from OPUS."""
        self._on_em27_error(str(error))

    def _measuring_end(self) -> None:
        """Move onto the next measurement or perform another measurement here."""
        self.current_measurement_count += 1
        if self.current_measurement_count == self.current_measurement.measurements:
            self.start_next_move()
        else:
            self.repeat_measuring()


if __name__ == "__main__":
    # Generate state diagram for ScriptRunner
    from statemachine.contrib.diagram import DotGraphMachine

    import finesse

    graph = DotGraphMachine(ScriptRunner)

    doc_dir = Path(finesse.__file__).parent.parent / "docs"
    graph().write_png(str(doc_dir / "script_runner_graph.png"))
