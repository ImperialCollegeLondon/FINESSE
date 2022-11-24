"""Contains code for a dialog to create and edit measure scripts."""

from typing import Any, Dict, List, Union

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from ..config import ANGLE_PRESETS


class ScriptEditDialog(QDialog):
    """A dialog to create and edit measure scripts."""

    def __init__(self, parent: QWidget) -> None:
        """Create a new ScriptEditDialog."""
        super().__init__(parent)
        self.setWindowTitle("Edit measurement script")

        self.count = CountWidget()
        self.sequence = SequenceWidget()

        layout = QVBoxLayout()
        layout.addWidget(self.count)
        layout.addWidget(self.sequence)

        self.setLayout(layout)


class CountWidget(QWidget):
    """A widget with QSpinBox labelled "Count"."""

    def __init__(self) -> None:
        """Create a new CountWidget."""
        super().__init__()

        layout = QFormLayout()

        self.count = QSpinBox()
        self.count.setMinimum(1)
        self.count.setMaximum(9999)
        layout.addRow("Count:", self.count)

        self.setLayout(layout)

    def value(self) -> int:
        """Get the value of the QSpinBox."""
        return self.count.value()


class SequenceModel(QAbstractTableModel):
    """Provides a model of the sequence data for the QTableView."""

    _COLUMNS = ("angle", "count")
    """The names of the data columns."""

    def __init__(self, sequence: List[Dict[str, Any]]) -> None:
        """Create a new SequenceModel.

        Args:
            sequence: A list of dicts containing "angle" and "count" fields
        """
        super().__init__()
        self._sequence = sequence

    def data(
        self,
        index: Union[QModelIndex, QPersistentModelIndex],
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """Provides the model's data."""
        # Column 0 is angle, column 1 is count
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._sequence[index.row()][SequenceModel._COLUMNS[index.column()]]
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
        # For column names we use Angle and Count
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

    def __init__(self) -> None:
        """Create a new SequenceWidget."""
        super().__init__()

        self.table = QTableView()

        self.sequence: List[Dict[str, Any]] = []
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

    def add_instruction(self, angle: Union[str, float], count: int) -> None:
        """Add a new measure instruction to the sequence.

        Args:
            angle: Target angle as a float or a string corresponding to a preset
            count: Number of times to take a measurement at this angle
        """
        self.sequence.append({"angle": angle, "count": count})
        self.model.layoutChanged.emit()  # type: ignore
        self.table.scrollToBottom()

    def delete_selected(self) -> None:
        """Removes the currently selected instructions from the table."""
        selected = [idx.row() for idx in self.table.selectionModel().selectedRows()]
        for row in sorted(selected, reverse=True):
            self.model.beginRemoveRows(QModelIndex(), row, row)
            self.sequence.pop(row)
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
        self.count = CountWidget()
        layout.addWidget(self.count)

        # Add buttons for preset angles (e.g. zenith, nadir, etc.)
        self.group = QButtonGroup()
        self.group.buttonClicked.connect(self._preset_clicked)  # type: ignore
        for preset in ANGLE_PRESETS:
            btn = QPushButton(preset.upper())
            self.group.addButton(btn)
            layout.addWidget(btn)

        # Add button and spinbox for going to a specific angle
        self.angle = QSpinBox()
        self.angle.setMinimum(0)
        self.angle.setMaximum(359)
        goto = QPushButton("GOTO")
        goto.clicked.connect(self._goto_clicked)  # type: ignore
        layout.addWidget(self.angle)
        layout.addWidget(goto)

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

        delete = QPushButton("Delete")
        delete.clicked.connect(sequence.delete_selected)  # type: ignore

        layout = QVBoxLayout()
        layout.addWidget(delete)
        self.setLayout(layout)
