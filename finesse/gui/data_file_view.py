"""Provides a panel which lets the user start and stop recording of data files."""
from pubsub import pub
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QPushButton

from ..config import DEFAULT_DATA_FILE_PATH
from .path_widget import SavePathWidget


class DataFileControl(QGroupBox):
    """A panel which lets the user start and stop recording of data files."""

    def __init__(self) -> None:
        """Create a new DataFileControl."""
        super().__init__("Data file")

        layout = QHBoxLayout()
        layout.addWidget(QLabel("Path"))

        self.save_path_widget = SavePathWidget(
            extension="csv",
            parent=self,
            caption="Choose destination for data file",
            dir=str(DEFAULT_DATA_FILE_PATH),
        )
        """Lets the user choose the destination for data files."""
        layout.addWidget(self.save_path_widget)

        # TODO: Enable/disable this on DP9800 connect/disconnect
        self.record_btn = QPushButton("Start recording")
        """Toggles recording state."""
        self.record_btn.clicked.connect(self._toggle_recording)  # type: ignore
        layout.addWidget(self.record_btn)

        self.setLayout(layout)

    def _toggle_recording(self) -> None:
        """Starts or stops recording as needed."""
        if self.record_btn.text() == "Stop recording":
            self.record_btn.setText("Start recording")
            pub.sendMessage("data_file.close")
        elif file_path := self.save_path_widget.try_get_path():
            self.record_btn.setText("Stop recording")
            pub.sendMessage("data_file.open", path=file_path)
