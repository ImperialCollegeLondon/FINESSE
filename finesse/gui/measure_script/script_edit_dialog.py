"""Contains code for a dialog to create and edit measure scripts."""

import logging
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import yaml
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from ...config import DEFAULT_SCRIPT_PATH
from ..error_message import show_error_message
from ..path_widget import SavePathWidget
from .count_widget import CountWidget
from .script import Script
from .sequence_widget import SequenceWidget


class ScriptEditDialog(QDialog):
    """A dialog to create and edit measure scripts."""

    def __init__(self, parent: QWidget, script: Optional[Script] = None) -> None:
        """Create a new ScriptEditDialog.

        Args:
            parent: Parent widget
            script: A loaded measure script or None
        """
        super().__init__(parent)
        self.setWindowTitle("Edit measurement script")

        initial_save_path: Optional[Path] = None
        if script:
            self.count = CountWidget("Repeats", script.repeats)
            self.sequence_widget = SequenceWidget(script.sequence)
            initial_save_path = script.path
        else:
            self.count = CountWidget("Repeats")
            self.sequence_widget = SequenceWidget()
        self.script_path = SavePathWidget(
            initial_save_path,
            extension="yaml",
            parent=self,
            caption="Choose destination for measure script",
            dir=str(DEFAULT_SCRIPT_PATH),
        )

        # Put a label next to the script path
        script_widget = QWidget()
        script_layout = QFormLayout()
        script_layout.addRow("Script file path:", self.script_path)
        script_widget.setLayout(script_layout)

        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.accepted.connect(self._try_accept)
        self.buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.count)
        layout.addWidget(self.sequence_widget)
        layout.addWidget(script_widget)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

    def _try_accept(self) -> None:
        if self._try_save():
            self.accept()

    def _try_save(self) -> bool:
        """Try to save measurement script.

        Returns:
            True if file saved successfully (or no data to save), false otherwise
        """
        # If there aren't any instructions, there isn't anything to save
        if not self.sequence_widget.sequence:
            return True

        file_path = self.script_path.try_get_path()
        if not file_path:
            # User didn't choose a file path
            return False

        logging.info(f"Saving file to {file_path}")

        script = {
            "repeats": self.count.value(),
            "sequence": [asdict(seq) for seq in self.sequence_widget.sequence],
        }

        try:
            with open(file_path, "w") as f:
                yaml.safe_dump(script, f)
        except Exception as e:
            show_error_message(
                self, f"Error occurred while saving file {file_path}:\n{str(e)}"
            )
            return False

        return True

    def closeEvent(self, event: QCloseEvent) -> None:
        """Check for unsaved data and if necessary save it."""
        # Just close if the dialog is already closed or there aren't any instructions
        # See bug: https://bugreports.qt.io/browse/QTBUG-43344
        if not self.isVisible() or not self.sequence_widget.sequence:
            self.setResult(QDialog.DialogCode.Accepted)
            return

        msg_box = QMessageBox(
            QMessageBox.Icon.Question,
            "Changes not saved",
            "Do you want to save your changes?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )

        ret = msg_box.exec()
        if ret == QMessageBox.StandardButton.Discard:
            self.setResult(QDialog.DialogCode.Rejected)
        elif ret == QMessageBox.StandardButton.Save and self._try_save():
            self.setResult(QDialog.DialogCode.Accepted)
        else:
            # User cancelled; leave this dialog open
            event.ignore()
