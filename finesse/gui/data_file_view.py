"""Provides a panel which lets the user start and stop recording of data files."""
from pathlib import Path

from pubsub import pub
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QSizePolicy,
)

from ..config import DEFAULT_DATA_FILE_PATH
from .path_widget import SavePathWidget


class DataFileControl(QGroupBox):
    """A panel which lets the user start and stop recording of data files."""

    def __init__(self) -> None:
        """Create a new DataFileControl."""
        super().__init__("Data file")

        layout = QHBoxLayout()

        self.save_path_widget = SavePathWidget(
            extension="csv",
            parent=self,
            caption="Choose destination for data file",
            dir=str(DEFAULT_DATA_FILE_PATH),
        )
        """Lets the user choose the destination for data files."""
        layout.addWidget(self.save_path_widget)

        self.record_btn = QPushButton("Start recording")
        """Toggles recording state."""
        self.record_btn.clicked.connect(self._toggle_recording)
        self.record_btn.setEnabled(False)
        layout.addWidget(self.record_btn)

        self.setLayout(layout)

        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed,
        )

        # Backend indicates when necessary devices are all connected/disconnected
        pub.subscribe(self._on_data_file_enable, "data_file.enable")
        pub.subscribe(self._on_data_file_disable, "data_file.disable")

        # Update GUI on file open/close
        pub.subscribe(self._on_file_open, "data_file.open")
        pub.subscribe(self._on_file_close, "data_file.close")

        # Show an error message if writing fails
        pub.subscribe(self._show_error_message, "data_file.error")

    def _on_data_file_enable(self) -> None:
        self.record_btn.setEnabled(True)

    def _on_data_file_disable(self) -> None:
        self.record_btn.setEnabled(False)

        if self.record_btn.text() == "Stop recording":
            QMessageBox.warning(
                self,
                "Device closed",
                "Device was closed unexpectedly during data recording. "
                "Recording will now stop.",
            )

    def _on_file_open(self, path: Path) -> None:
        self.save_path_widget.setEnabled(False)
        self.record_btn.setText("Stop recording")

    def _on_file_close(self) -> None:
        self.save_path_widget.setEnabled(True)
        self.record_btn.setText("Start recording")

    def _user_confirms_overwrite(self, path: Path) -> bool:
        """Confirm with the user whether to overwrite file via a dialog."""
        response = QMessageBox.question(
            self,
            "Overwrite file?",
            f"The file {path.name} already exists. Would you like to overwrite it?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return response == QMessageBox.StandardButton.Yes

    def _try_start_recording(self, path: Path) -> None:
        """Start recording if path doesn't exist or user accepts overwriting it."""
        if not path.exists() or self._user_confirms_overwrite(path):
            pub.sendMessage("data_file.open", path=path)

    def _toggle_recording(self) -> None:
        """Starts or stops recording as needed."""
        if self.record_btn.text() == "Stop recording":
            pub.sendMessage("data_file.close")
        elif path := self.save_path_widget.try_get_path():
            self._try_start_recording(path)

    def _show_error_message(self, error: BaseException) -> None:
        """Show an error dialog."""
        msg_box = QMessageBox(
            QMessageBox.Icon.Critical,
            "Error writing to file",
            f"An error occurred while writing the data file: {str(error)}",
            QMessageBox.StandardButton.Ok,
            self,
        )
        msg_box.exec()
