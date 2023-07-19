"""Provides a panel which lets the user start and stop recording of data files."""
from datetime import datetime
from pathlib import Path

from pubsub import pub
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
)

from ..config import DEFAULT_DATA_FILE_PATH
from .path_widget import OpenDirectoryWidget


class DataFileControl(QGroupBox):
    """A panel which lets the user start and stop recording of data files."""

    def __init__(self) -> None:
        """Create a new DataFileControl."""
        super().__init__("Data file")

        layout = QHBoxLayout()

        self.open_dir_widget = OpenDirectoryWidget(
            parent=self,
            caption="Choose destination for data file",
            dir=str(DEFAULT_DATA_FILE_PATH),
        )
        """Lets the user choose the destination for data files."""
        layout.addWidget(QLabel("Destination directory:"))
        layout.addWidget(self.open_dir_widget)

        self.filename_prefix_widget = QLineEdit()
        layout.addWidget(QLabel("Filename prefix:"))
        layout.addWidget(self.filename_prefix_widget)

        self.record_btn = QPushButton("Start recording")
        """Toggles recording state."""
        self.record_btn.clicked.connect(self._toggle_recording)
        layout.addWidget(self.record_btn)

        self.setLayout(layout)

        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed,
        )

        # Update GUI on file open/close
        pub.subscribe(self._on_file_open, "data_file.open")
        pub.subscribe(self._on_file_close, "data_file.close")

        # Show an error message if writing fails
        pub.subscribe(self._show_error_message, "data_file.error")

    def _on_file_open(self, path: Path) -> None:
        self.open_dir_widget.setEnabled(False)
        self.filename_prefix_widget.setEnabled(False)
        self.record_btn.setText("Stop recording")

    def _on_file_close(self) -> None:
        self.open_dir_widget.setEnabled(True)
        self.filename_prefix_widget.setEnabled(True)
        self.record_btn.setText("Start recording")

    def _try_get_data_file_path(self) -> Path | None:
        dest_dir = self.open_dir_widget.try_get_path()
        if not dest_dir:
            # User cancelled
            return None

        filename_prefix = self.filename_prefix_widget.text()
        if not filename_prefix:
            # Check that the user has added a prefix
            QMessageBox(
                QMessageBox.Icon.Critical,
                "No filename prefix specified",
                "The filename prefix cannot be blank.",
            ).exec()
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = dest_dir / f"{filename_prefix}_{timestamp}.csv"
        if path.exists():
            # It's unlikely that the file will already exist, but let's make doubly sure
            QMessageBox(
                QMessageBox.Icon.Critical,
                "File already exists",
                "The destination file already exists.",
            ).exec()
            return None

        return path

    def _toggle_recording(self) -> None:
        """Starts or stops recording as needed."""
        if self.record_btn.text() == "Stop recording":
            pub.sendMessage("data_file.close")
        elif path := self._try_get_data_file_path():
            pub.sendMessage("data_file.open", path=path)

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
