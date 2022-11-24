"""Contains a panel for loading and editing measure scripts."""
from typing import Optional

from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton

from .script_edit_dialog import ScriptEditDialog


class ScriptControl(QGroupBox):
    """A panel for loading and editing measure scripts."""

    def __init__(self) -> None:
        """Create a new ScriptControl."""
        super().__init__("Script control")

        create_btn = QPushButton("Create new script")
        create_btn.clicked.connect(self._create_btn_clicked)  # type: ignore

        layout = QHBoxLayout()
        layout.addWidget(create_btn)

        self.setLayout(layout)

        self.dialog: Optional[ScriptEditDialog] = None

    def _create_btn_clicked(self) -> None:
        if not self.dialog or self.dialog.isHidden():
            self.dialog = ScriptEditDialog(self.window())
            self.dialog.show()
