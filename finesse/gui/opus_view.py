"""Panel and widgets related to the control of the OPUS interferometer."""
import logging
from functools import partial
from typing import Dict, Optional

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QVBoxLayout

COMMANDS = {
    "status": "opusrs/stat.htm",
    "connect": "opusrs/cmd.htm?opusrsconnect",
    "start": "opusrs/cmd.htm?opusrsstart",
    "stop": "opusrs/cmd.htm?opusrsstop",
    "cancel": "opusrs/cmd.htm?opusrscancel",
    "opus": "TBC",
}


class OPUSControl(QGroupBox):
    """Class that monitors and control the OPUS interferometer."""

    def __init__(self, ip: str, commands: Optional[Dict[str, str]] = None) -> None:
        """Creates the widgets to monitor and control the OPUS interferometer.

        Args:
            ip: IP for connecting to the OPUS system
            commands: Commands to use to construct the action urls
        """
        super().__init__("OPUS client view")

        self.ip = ip
        self.commands = commands if commands is not None else COMMANDS
        self.status: QWebEngineView

        layout = self._create_controls()
        self.setLayout(layout)

    def _create_controls(self) -> QHBoxLayout:
        """Creates the controls for comunicating with the interferometer.

        Returns:
            QHBoxLayout: The layout with the buttons.
        """
        main_layout = QHBoxLayout()
        main_layout.addLayout(self._create_buttons())
        main_layout.addLayout(self._create_status_page())
        return main_layout

    def _create_buttons(self) -> QVBoxLayout:
        """Creates the buttons.

        Returns:
            QHBoxLayout: The layout with the buttons.
        """
        btn_layout = QVBoxLayout()

        button = QPushButton("Status")
        button.clicked.connect(self.display_status)  # type: ignore
        btn_layout.addWidget(button)

        for name in set(self.commands.keys()) - {"status", "opus"}:

            button = QPushButton(name.capitalize())
            button.clicked.connect(  # type: ignore
                partial(self.on_button_clicked, action=name.lower())
            )
            btn_layout.addWidget(button)

        button = QPushButton("OPUS")
        button.clicked.connect(self.open_opus)  # type: ignore
        btn_layout.addWidget(button)

        btn_layout.addStretch()

        return btn_layout

    def _create_status_page(self) -> QVBoxLayout:
        """Creates the status_page.

        Returns:
            QHBoxLayout: The layout with the buttons.
        """
        status_page = QGroupBox("Status")
        self.status = QWebEngineView()

        _layout = QVBoxLayout()
        _layout.addWidget(self.status)
        status_page.setLayout(_layout)

        layout = QVBoxLayout()
        layout.addWidget(status_page)
        return layout

    def url(self, action: str) -> str:
        """Builds an URL out of the ip and the action.

        Args:
            action (str): The action to use.

        Returns:
            str: The constructed URL
        """
        return f"http://{self.ip}/{self.commands[action]}"

    def on_button_clicked(self, action: str) -> None:
        """Execute the given action by sending a message to the appropriate topic.

        TODO: Here assuming we are going to use pubsub or equivalent to send messages
        around and communicate between backend and front end.

        Args:
            action: Action to be executed.
        """
        logging.info(f"Action '{self.url(action)}' executed!")

    def display_status(self) -> None:
        """Retrieves and displays the new status."""
        logging.info("Getting OPUS status!")
        self.status.load(QUrl(self.url("status")))
        self.status.show()

    def open_opus(self) -> None:
        """Opens OPUS front end somewhere else.

        TODO: No idea what this is supposed to do.
        """
        logging.info("Going to OPUS!")


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    window = QMainWindow()
    opus = OPUSControl("127.0.0.1", commands=COMMANDS)
    window.setCentralWidget(opus)
    window.show()
    app.exec()
