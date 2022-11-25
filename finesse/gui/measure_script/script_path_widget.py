"""Provides a widget for choosing the path to a measure script."""
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QWidget,
)


class ScriptPathWidget(QWidget):
    """A widget containing a text box with a file path and a browse button."""

    def __init__(self) -> None:
        """Create a new ChoosePathWidget."""
        super().__init__()

        label = QLabel("Script file path:")
        label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.line_edit = QLineEdit()
        browse = QPushButton("&Browse...")
        browse.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        browse.clicked.connect(self._browse_clicked)  # type: ignore

        layout = QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.line_edit)
        layout.addWidget(browse)
        self.setLayout(layout)

    def _browse_clicked(self) -> None:
        self.line_edit.setText(self._get_save_file_name())

    def _get_save_file_name(self) -> str:
        # TODO: Automatically add .yaml extension
        filename, _ = QFileDialog.getSaveFileName(
            self,
            caption="Choose destination path",
            dir=str(Path.home()),
            filter="*.yaml",
        )
        return filename

    def get_path(self) -> Optional[Path]:
        """Get the path of the chosen file.

        If the path hasn't yet been set, a QFileDialog is opened to let the user choose
        one.
        """
        txt = self.line_edit.text()
        if txt:
            return Path(txt)

        # ...otherwise the user hasn't chosen a path. Let them do it now.
        filename = self._get_save_file_name()

        # Return None if no path selected
        return Path(filename) if filename else None
