"""Contains code for a dialog to create and edit measure scripts."""

import logging
from pathlib import Path
from typing import Any, List, Optional, Union

import yaml
from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from ...config import ANGLE_PRESETS, DEFAULT_SCRIPT_PATH
from ..error_message import show_error_message
from .parse import Measurement, Script
from .script_path_widget import ScriptPathWidget


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

        if script:
            self.count = CountWidget("Repeats", script.repeats)
            self.sequence_widget = SequenceWidget(script.sequence)
            self.script_path = SaveScriptPathWidget(script.path)
        else:
            self.count = CountWidget("Repeats")
            self.sequence_widget = SequenceWidget()
            self.script_path = SaveScriptPathWidget()

        # Put a label next to the script path
        script_widget = QWidget()
        script_layout = QFormLayout()
        script_layout.addRow("Script file path:", self.script_path)
        script_widget.setLayout(script_layout)

        buttonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttonBox.setCenterButtons(True)
        buttonBox.accepted.connect(self._try_accept)  # type: ignore
        buttonBox.rejected.connect(self.reject)  # type: ignore

        layout = QVBoxLayout()
        layout.addWidget(self.count)
        layout.addWidget(self.sequence_widget)
        layout.addWidget(script_widget)
        layout.addWidget(buttonBox)

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
            "sequence": [seq.to_dict() for seq in self.sequence_widget.sequence],
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


class CountWidget(QWidget):
    """A widget with labelled QSpinBox."""

    def __init__(self, label: str, initial_count: int = 1) -> None:
        """Create a new CountWidget.

        Args:
            label: A string label for the control
            initial_count: The initial value of the QSpinBox
        """
        super().__init__()

        self.count = QSpinBox()
        self.count.setMinimum(1)
        self.count.setMaximum(9999)
        self.count.setValue(initial_count)

        layout = QFormLayout()
        layout.addRow(f"{label}:", self.count)
        self.setLayout(layout)

    def value(self) -> int:
        """Get the value of the QSpinBox."""
        return self.count.value()


class SequenceModel(QAbstractTableModel):
    """Provides a model of the sequence data for the QTableView."""

    _COLUMNS = ("angle", "measurements")
    """The names of the data columns."""

    def __init__(self, sequence: List[Measurement]) -> None:
        """Create a new SequenceModel.

        Args:
            sequence: A list of Measurements
        """
        super().__init__()
        self._sequence = sequence

    def data(
        self,
        index: Union[QModelIndex, QPersistentModelIndex],
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """Provides the model's data."""
        # Column 0 is angle, column 1 is measurements
        if role == Qt.ItemDataRole.DisplayRole:
            value = getattr(
                self._sequence[index.row()], SequenceModel._COLUMNS[index.column()]
            )
            if isinstance(value, float):
                return f"{value:.0f}°"
            return value

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """Provides header names for the model's data."""
        # For column names we use Angle and Measurements
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return SequenceModel._COLUMNS[section].title()

        return super().headerData(section, orientation, role)

    def rowCount(self, *args: Any, **kwargs: Any) -> int:
        """Get the number of data rows."""
        return len(self._sequence)

    def columnCount(self, *args: Any, **kwargs: Any) -> int:
        """Get the number of data columns."""
        return 2


class SequenceWidget(QWidget):
    """A widget with a table of measure instructions and controls to modify them."""

    def __init__(self, sequence: Optional[List[Measurement]] = None) -> None:
        """Create a new SequenceWidget."""
        super().__init__()

        self.table = QTableView()

        self.sequence = sequence if sequence else []
        """The sequence of measure instructions as a list of angles and counts."""

        self.model = SequenceModel(self.sequence)
        self.table.setModel(self.model)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self.buttons = SequenceButtons(self)

        # Put the table on the left and the buttons on the right
        layout = QHBoxLayout()
        layout.addWidget(self.table)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    def add_instruction(self, angle: Union[str, float], measurements: int) -> None:
        """Add a new measure instruction to the sequence.

        Args:
            angle: Target angle as a float or a string corresponding to a preset
            measurements: Number of times to take a measurement at this angle
        """
        self.sequence.append(Measurement(angle, measurements))
        self.model.layoutChanged.emit()  # type: ignore
        self.table.scrollToBottom()

    def _get_selected_rows(self, reverse: bool = False) -> List[int]:
        """Get the indices of the currently selected rows in the table.

        Args:
            reverse: Whether to return the indices in reverse order
        """
        selected = [idx.row() for idx in self.table.selectionModel().selectedRows()]
        selected.sort(reverse=reverse)
        return selected

    def _swap_rows(self, lower: int, higher: int) -> None:
        """Swap the rows specified by two indices."""
        # For some reason if these arguments are the wrong way round, Qt crashes
        assert higher > lower

        self.model.beginMoveRows(QModelIndex(), higher, higher, QModelIndex(), lower)
        self.sequence[lower], self.sequence[higher] = (
            self.sequence[higher],
            self.sequence[lower],
        )
        self.model.endMoveRows()

    def move_selected_up(self) -> None:
        """Move the currently selected instructions up one row."""
        selected = self._get_selected_rows()
        if not selected or selected[0] == 0:
            # We can't move up if the topmost item is selected
            return

        # Swap each element with the one above it
        for row in selected:
            self._swap_rows(row - 1, row)

    def move_selected_down(self) -> None:
        """Move the currently selected instructions down one row."""
        selected = self._get_selected_rows(reverse=True)
        if not selected or selected[0] == len(self.sequence) - 1:
            # We can't move down if the bottom item is selected
            return

        # Swap each element with the one below it
        for row in selected:
            self._swap_rows(row, row + 1)

    def delete_selected(self) -> None:
        """Remove the currently selected instructions from the table."""
        for row in self._get_selected_rows(reverse=True):
            self.model.beginRemoveRows(QModelIndex(), row, row)
            self.sequence.pop(row)
            self.model.endRemoveRows()

    def delete_all(self) -> None:
        """Delete all instructions from the table."""
        self.model.beginRemoveRows(QModelIndex(), 0, len(self.sequence) - 1)
        self.sequence.clear()
        self.model.endRemoveRows()


class SequenceButtons(QWidget):
    """Buttons for changing the sequence of instructions."""

    def __init__(self, sequence: SequenceWidget) -> None:
        """Create a new SequenceButtons."""
        super().__init__()

        add_buttons = AddButtons(sequence)
        change_buttons = ChangeButtons(sequence)

        layout = QVBoxLayout()
        layout.addWidget(add_buttons)
        layout.addWidget(change_buttons)
        self.setLayout(layout)


class AddButtons(QGroupBox):
    """Buttons for adding new instructions."""

    def __init__(self, sequence: SequenceWidget) -> None:
        """Create a new AddButtons."""
        super().__init__("Add instruction")
        self.sequence = sequence

        layout = QVBoxLayout()

        # The number of times to repeat this measurement
        self.count = CountWidget("Measurements")
        layout.addWidget(self.count)

        # Add buttons for preset angles (e.g. zenith, nadir, etc.)
        self.group = QButtonGroup()
        self.group.buttonClicked.connect(self._preset_clicked)  # type: ignore
        for preset in ANGLE_PRESETS:
            btn = QPushButton(preset.upper())
            self.group.addButton(btn)
            layout.addWidget(btn)

        # Add button and spinbox for going to a specific angle. Put them next to each
        # other on the same row.
        goto_layout = QHBoxLayout()
        self.angle = QSpinBox()
        self.angle.setSuffix("°")
        self.angle.setMinimum(0)
        self.angle.setMaximum(270)
        goto = QPushButton("GOTO")
        goto.clicked.connect(self._goto_clicked)  # type: ignore
        goto_layout.addWidget(self.angle)
        goto_layout.addWidget(goto)

        # Add these widgets to the main layout
        goto_widgets = QWidget()
        goto_widgets.setLayout(goto_layout)
        layout.addWidget(goto_widgets)

        self.setLayout(layout)

    def _goto_clicked(self) -> None:
        self.sequence.add_instruction(float(self.angle.value()), self.count.value())

    def _preset_clicked(self, btn: QPushButton) -> None:
        self.sequence.add_instruction(btn.text().lower(), self.count.value())


class ChangeButtons(QGroupBox):
    """Buttons for modifying existing measure instructions."""

    def __init__(self, sequence: SequenceWidget) -> None:
        """Create a new ChangeButtons."""
        super().__init__("Modify instructions")

        up = QPushButton("Up")
        up.clicked.connect(sequence.move_selected_up)  # type: ignore

        down = QPushButton("Down")
        down.clicked.connect(sequence.move_selected_down)  # type: ignore

        delete = QPushButton("Delete")
        delete.clicked.connect(sequence.delete_selected)  # type: ignore

        clear = QPushButton("Clear")
        clear.clicked.connect(sequence.delete_all)  # type: ignore

        layout = QVBoxLayout()
        layout.addWidget(up)
        layout.addWidget(down)
        layout.addWidget(delete)
        layout.addWidget(clear)
        self.setLayout(layout)


class SaveScriptPathWidget(ScriptPathWidget):
    """A widget that lets the user choose the path to save a script."""

    def try_get_path_from_dialog(self) -> Optional[Path]:
        """Try to get the path to save the file to by opening a dialog."""
        dialog = QFileDialog(
            self,
            caption="Choose destination path",
            directory=str(DEFAULT_SCRIPT_PATH),
            filter="*.yaml",
        )
        dialog.setDefaultSuffix("yaml")

        if dialog.exec():
            return Path(dialog.selectedFiles()[0])
        return None
