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
        browse.clicked.connect(self._browse_clicked)  # type: ignore

        layout = QHBoxLayout()
        layout.addWidget(self.line_edit)
        layout.addWidget(browse)
        self.setLayout(layout)

    def _browse_clicked(self) -> None:
        self.line_edit.setText(self.get_file_name())

    @abstractmethod
    def get_file_name(self) -> str:
        """Get the file name by raising a dialog."""
        raise NotImplementedError()

    def try_get_path(self) -> Optional[Path]:
        """Get the path of the chosen file.

        If the path hasn't yet been set, a QFileDialog is opened to let the user choose
        one.

        Returns:
            The selected file path or None if the user has cancelled
        """
        txt = self.line_edit.text()
        if txt:
            return Path(txt)

        # ...otherwise the user hasn't chosen a path. Let them do it now.
        filename = self.get_file_name()
        if filename:
            self.line_edit.setText(filename)
            return Path(filename)

        # No path selected
        return None
