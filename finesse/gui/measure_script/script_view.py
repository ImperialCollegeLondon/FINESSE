"""Contains a panel for loading and editing measure scripts."""
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QFileDialog, QGroupBox, QHBoxLayout, QPushButton

from ..error_message import show_error_message
from .parse import ParseError
from .script_edit_dialog import ScriptEditDialog


class ScriptControl(QGroupBox):
    """A panel for loading and editing measure scripts."""

    def __init__(self) -> None:
        """Create a new ScriptControl."""
        super().__init__("Script control")

        create_btn = QPushButton("Create new script")
        create_btn.clicked.connect(self._show_edit_dialog)  # type: ignore

        edit_btn = QPushButton("Edit script")
        edit_btn.clicked.connect(self._edit_btn_clicked)  # type: ignore

        layout = QHBoxLayout()
        layout.addWidget(create_btn)
        layout.addWidget(edit_btn)
        self.setLayout(layout)

        self.dialog: Optional[ScriptEditDialog] = None

    def _show_edit_dialog(self, file_path: Optional[Path] = None) -> None:
        """Create and show edit dialog if it doesn't exist."""
        if not self.dialog or self.dialog.isHidden():
            self.dialog = ScriptEditDialog(self.window(), file_path)
            self.dialog.show()

    def _edit_btn_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, caption="Choose script file", dir=str(Path.home()), filter="*.yaml"
        )

        if not file_path:
            # User closed dialog
            return

        try:
            self._show_edit_dialog(Path(file_path))
        except OSError as e:
            show_error_message(self, f"Error: Could not read {file_path}: {str(e)}")
        except ParseError:
            show_error_message(self, f"Error: {file_path} is in an invalid format")
