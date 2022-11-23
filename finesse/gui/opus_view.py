"""Panel and widgets related to the control of the OPUS interferometer."""
import logging
from functools import partial

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QVBoxLayout


class OPUSControl(QGroupBox):
    """Class that monitors and control the OPUS interferometer."""

    _btn_actions = ("Status", "Cancel", "Start", "Stop", "Connect", "OPUS")
    _status_info = ("Status code", "Description", "Error code", "Error description")

    def __init__(self) -> None:
        """Creates the widgets to monitor and control the OPUS interferometer."""
        super().__init__("OPUS client view")

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
        for action in self._btn_actions:

            button = QPushButton(action)
            button.released.connect(  # type: ignore
                partial(self.on_button_clicked, action=action)
            )
            btn_layout.addWidget(button)

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

    def on_button_clicked(self, action: str) -> None:
        """Execute the given action by sending a message to the appropriate topic.

        TODO: Here assuming we are going to use pubsub or equivalent to send messages
        around and communicate between backend and front end.

        Args:
            action: Action to be executed.
        """
        logging.info(f"Action '{action}' executed!")

    def display_status(self, url: str) -> None:
        """Displays the new status provided by the url.

        Args:
            url: Where information with the new status is contained.
        """
        self.status.load(QUrl(url))
        self.status.show()


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    window = QMainWindow()
    opus = OPUSControl()
    window.setCentralWidget(opus)
    window.show()
    app.exec()
