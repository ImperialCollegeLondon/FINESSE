"""Contains a panel for loading and editing measure scripts."""
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton


class ScriptControl(QGroupBox):
    """A panel for loading and editing measure scripts."""

    def __init__(self) -> None:
        """Create a new ScriptControl."""
        super().__init__("Script control")

        create_btn = QPushButton("Create new script")

        layout = QHBoxLayout()
        layout.addWidget(create_btn)

        self.setLayout(layout)
