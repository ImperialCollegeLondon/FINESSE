"""Contains a panel for loading and editing measure scripts."""
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QFileDialog, QGroupBox, QHBoxLayout, QPushButton

from ...config import DEFAULT_SCRIPT_PATH
from .parse import try_load_script
from .script_edit_dialog import ScriptEditDialog


class ScriptControl(QGroupBox):
    """A panel for loading and editing measure scripts."""

    def __init__(self) -> None:
        """Create a new ScriptControl."""
        super().__init__("Script control")

        create_btn = QPushButton("Create new script")
        create_btn.clicked.connect(self._create_btn_clicked)  # type: ignore

        edit_btn = QPushButton("Edit script")
        edit_btn.clicked.connect(self._edit_btn_clicked)  # type: ignore

        layout = QHBoxLayout()
        layout.addWidget(create_btn)
        layout.addWidget(edit_btn)
        self.setLayout(layout)

        self.dialog: Optional[ScriptEditDialog] = None

    def _create_btn_clicked(self) -> None:
        # If there is no open dialog, then create a new one
        if not self.dialog or self.dialog.isHidden():
            self.dialog = ScriptEditDialog(self.window())
            self.dialog.show()

    def _edit_btn_clicked(self) -> None:
        # If there's already a dialog open, try to close it first to save data etc.
        if self.dialog and not self.dialog.close():
            return

        # Ask user to choose script file to edit
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            caption="Choose script file to edit",
            dir=str(DEFAULT_SCRIPT_PATH),
            filter="*.yaml",
        )

        if not file_path:
            # User closed dialog
            return

        script = try_load_script(self, Path(file_path))
        if not script:
            # An error occurred while loading script
            return

        # Create new dialog showing contents of script
        self.dialog = ScriptEditDialog(self.window(), script)
        self.dialog.show()
