"""Provides a widget for choosing the path to a measure script."""
from abc import abstractmethod
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QSizePolicy, QWidget


class ScriptPathWidget(QWidget):
    """A widget containing a text box with a file path and a browse button."""

    def __init__(self, file_path: Optional[Path] = None) -> None:
        """Create a new ChoosePathWidget.

        Args:
            file_path: Path to measure script to be edited or None to create new
        """
        super().__init__()

        self.line_edit = QLineEdit()
        """Indicates the current selected path."""

        self.line_edit.setReadOnly(True)
        if file_path:
            self.line_edit.setText(str(file_path))

        browse = QPushButton("&Browse...")
        browse.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        browse.clicked.connect(self._browse_clicked)

        layout = QHBoxLayout()
        layout.addWidget(self.line_edit)
        layout.addWidget(browse)
        self.setLayout(layout)

    def _browse_clicked(self) -> None:
        filename = self.try_get_path_from_dialog()
        if filename:
            self.set_path(filename)

    @abstractmethod
    def try_get_path_from_dialog(self) -> Optional[Path]:
        """Try to get the file name by raising a dialog."""

    def try_get_path(self) -> Optional[Path]:
        """Try to get the path of the chosen file for this widget.

        If the path hasn't yet been set, a QFileDialog is opened to let the user choose
        one.

        Returns:
            The selected file path or None if the user has cancelled
        """
        txt = self.line_edit.text()
        if txt:
            return Path(txt)

        # ...otherwise the user hasn't chosen a path. Let them do it now.
        filename = self.try_get_path_from_dialog()
        if filename:
            self.set_path(filename)
            return Path(filename)

        # No path selected
        return None

    def set_path(self, path: Path) -> None:
        """Set the path of this widget."""
        self.line_edit.setText(str(path))
