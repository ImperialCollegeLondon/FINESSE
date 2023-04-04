"""Contains a panel for loading and editing measure scripts."""
from pathlib import Path
from typing import Optional, cast

from PySide6.QtWidgets import QFileDialog, QGridLayout, QGroupBox, QPushButton

from ...config import DEFAULT_SCRIPT_PATH
from ...settings import settings
from ..path_widget import OpenPathWidget
from .script import Script
from .script_edit_dialog import ScriptEditDialog


def _get_previous_script_path() -> Optional[Path]:
    path = cast(str, settings.value("script/run_path", ""))
    return Path(path) if path else None


class ScriptControl(QGroupBox):
    """A panel for loading and editing measure scripts."""

    def __init__(self) -> None:
        """Create a new ScriptControl."""
        super().__init__("Script control")

        create_btn = QPushButton("Create new script")
        create_btn.clicked.connect(self._create_btn_clicked)

        edit_btn = QPushButton("Edit script")
        edit_btn.clicked.connect(self._edit_btn_clicked)

        self.script_path = OpenPathWidget(
            initial_file_path=_get_previous_script_path(),
            extension="yaml",
            parent=self,
            caption="Choose measure script to load",
            dir=str(DEFAULT_SCRIPT_PATH),
        )

        run_btn = QPushButton("Run script")
        run_btn.clicked.connect(self._run_btn_clicked)

        layout = QGridLayout()
        layout.addWidget(create_btn, 0, 0)
        layout.addWidget(edit_btn, 0, 1)
        layout.addWidget(self.script_path, 1, 0)
        layout.addWidget(run_btn, 1, 1)
        self.setLayout(layout)

        self.dialog: ScriptEditDialog
        """A dialog for editing the contents of a measure script."""

    def _create_btn_clicked(self) -> None:
        self.dialog = ScriptEditDialog(self.window())
        self.dialog.show()

    def _edit_btn_clicked(self) -> None:
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

        # Save to settings
        settings.setValue("script/run_path", str(file_path))

        # Run the script!
        script.run(self)
