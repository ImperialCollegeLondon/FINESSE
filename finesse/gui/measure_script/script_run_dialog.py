"""Provides a dialog to display the progress of a running measure script."""
from pubsub import pub
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from .script import Script, ScriptRunner


def get_total_steps(script: Script) -> int:
    """Get the total number of steps that a measure script will require.

    Each Measurement is repeated n times, plus we have to move into position once per
    Measurement. The whole script is repeated m times.
    """
    return script.repeats * sum(1 + m.measurements for m in script.sequence)


class ScriptRunDialog(QDialog):
    """A dialog to display the progress of a running measure script."""

    def __init__(self, parent: QWidget, script_runner: ScriptRunner) -> None:
        """Create a new ScriptRunDialog.

        Args:
            parent: The parent widget (window)
            script_runner: The ScriptRunner managing the current script
        """
        super().__init__(parent)
        self.setWindowTitle("Running measure script")
        self.setModal(True)

        layout = QVBoxLayout()
        self._progress_bar = QProgressBar()
        """Shows the progress of the measure script."""
        self._progress_bar.setMaximum(get_total_steps(script_runner.script))
        layout.addWidget(self._progress_bar)

        self._label = QLabel()
        """A text label describing what the measure script is currently doing."""
        layout.addWidget(self._label)

        buttonbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        buttonbox.rejected.connect(self.reject)
        self.rejected.connect(lambda: pub.sendMessage("measure_script.abort"))
        layout.addWidget(buttonbox)

        self.setLayout(layout)

        # Update dialog when measure script changes state
        pub.subscribe(self._on_start_moving, "measure_script.start_moving")
        pub.subscribe(self._on_start_measuring, "measure_script.start_measuring")

    def _update(self, script_runner: ScriptRunner, text: str) -> None:
        """Increment the progress bar and update the QLabel."""
        self._progress_bar.setValue(self._progress_bar.value() + 1)
        self._label.setText(
            f"Repeat {script_runner.measurement_iter.current_repeat + 1}"
            f" of {script_runner.script.repeats}: {text}"
        )

    def _on_start_moving(self, script_runner: ScriptRunner) -> None:
        angle = script_runner.current_measurement.angle
        if isinstance(angle, float):
            angle = f"{round(angle)}°"
        self._update(script_runner, f"Moving to {angle}")

    def _on_start_measuring(self, script_runner: ScriptRunner) -> None:
        self._update(
            script_runner,
            f"Carrying out measurement {script_runner.current_measurement_count + 1}"
            f" of {script_runner.current_measurement.measurements}",
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        """Abort the measure script."""
        self.reject()
