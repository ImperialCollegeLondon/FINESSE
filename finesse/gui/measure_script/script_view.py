"""Contains a panel for loading and editing measure scripts."""
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QFileDialog, QGridLayout, QGroupBox, QPushButton

from ...config import DEFAULT_SCRIPT_PATH
from .script import Script
from .script_edit_dialog import ScriptEditDialog
from .script_path_widget import ScriptPathWidget


class ScriptControl(QGroupBox):
    """A panel for loading and editing measure scripts."""

    def __init__(self) -> None:
        """Create a new ScriptControl."""
        super().__init__("Script control")

        create_btn = QPushButton("Create new script")
        create_btn.clicked.connect(self._create_btn_clicked)

        edit_btn = QPushButton("Edit script")
        edit_btn.clicked.connect(self._edit_btn_clicked)

        self.script_path = OpenScriptPathWidget()

        run_btn = QPushButton("Run script")
        run_btn.clicked.connect(self._run_btn_clicked)

        layout = QGridLayout()
        layout.addWidget(create_btn, 0, 0)
        layout.addWidget(edit_btn, 0, 1)
        layout.addWidget(self.script_path, 1, 0)
        layout.addWidget(run_btn, 1, 1)
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

        script = Script.try_load(self, Path(file_path))
        if not script:
            # An error occurred while loading script
            return

        # Create new dialog showing contents of script
        self.dialog = ScriptEditDialog(self.window(), script)
        self.dialog.show()

    def _run_btn_clicked(self) -> None:
        file_path = self.script_path.try_get_path()
        if not file_path:
            # User cancelled
            return

        script = Script.try_load(self, file_path)
        if not script:
            # Failed to load script
            return

        # Run the script!
        script.run(self)


class OpenScriptPathWidget(ScriptPathWidget):
    """A widget that lets the user choose the path to an existing script."""

    def try_get_path_from_dialog(self) -> Optional[Path]:
        """Try to get the path of the file to open by raising a dialog."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Choose script to load", str(DEFAULT_SCRIPT_PATH), "*.yaml"
        )

        return Path(filename) if filename else None
