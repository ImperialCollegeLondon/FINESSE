"""Contains a panel for loading and editing measure scripts."""
from pathlib import Path
from typing import Optional, cast

from pubsub import pub
from PySide6.QtWidgets import QFileDialog, QGridLayout, QGroupBox, QPushButton

from ...config import DEFAULT_SCRIPT_PATH, STEPPER_MOTOR_TOPIC
from ...em27_status import EM27Status
from ...event_counter import EventCounter
from ...settings import settings
from ..path_widget import OpenPathWidget
from .script import Script, ScriptRunner
from .script_edit_dialog import ScriptEditDialog
from .script_run_dialog import ScriptRunDialog


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
        run_btn.setEnabled(False)

        self._enable_counter = EventCounter(
            lambda: run_btn.setEnabled(True),
            lambda: run_btn.setEnabled(False),
            target_count=2,
            device_names=(STEPPER_MOTOR_TOPIC,),
        )
        """A counter to enable/disable the "Run" button."""

        layout = QGridLayout()
        layout.addWidget(create_btn, 0, 0)
        layout.addWidget(edit_btn, 0, 1)
        layout.addWidget(self.script_path, 1, 0)
        layout.addWidget(run_btn, 1, 1)
        self.setLayout(layout)

        # Monitor OPUS messages to enable/disable run button on connect/disconnect
        self._opus_connected = False
        pub.subscribe(self._on_opus_message, "opus.response")

        # Show/hide self.run_dialog on measure script begin/end
        pub.subscribe(self._show_run_dialog, "measure_script.begin")
        pub.subscribe(self._hide_run_dialog, "measure_script.end")

        self.edit_dialog: ScriptEditDialog
        """A dialog for editing the contents of a measure script."""

        self.run_dialog: ScriptRunDialog
        """A dialog showing the progress of a running measure script."""

    def _create_btn_clicked(self) -> None:
        self.edit_dialog = ScriptEditDialog(self.window())
        self.edit_dialog.show()

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
        self.edit_dialog = ScriptEditDialog(self.window(), script)
        self.edit_dialog.show()

    def _run_btn_clicked(self) -> None:
        """Try to run a measure script."""
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

    def _show_run_dialog(self, script_runner: ScriptRunner) -> None:
        """Create a new ScriptRunDialog and show it."""
        self.run_dialog = ScriptRunDialog(self.window(), script_runner)
        self.run_dialog.show()

    def _hide_run_dialog(self) -> None:
        """Hide and destroy the ScriptRunDialog."""
        self.run_dialog.hide()
        del self.run_dialog

    def _on_opus_message(
        self, status: EM27Status, text: str, error: Optional[tuple[int, str]]
    ) -> None:
        """Increase/decrease the enable counter when the EM27 connects/disconnects."""
        if status.is_connected == self._opus_connected:
            # The connection status hasn't changed
            return

        if status.is_connected:
            self._enable_counter.increment()
        else:
            self._enable_counter.decrement()

        self._opus_connected = status.is_connected
