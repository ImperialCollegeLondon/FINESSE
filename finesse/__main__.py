"""The main entry point to FINESSE."""
import sys

from PySide6.QtWidgets import QApplication, QMainWindow

from .gui.serial_view import SerialPortControl


def main() -> None:
    """Run FINESSE."""
    app = QApplication(sys.argv)

    window = QMainWindow()
    devices = {
        "ST10": {"port": "COM5", "baud_rate": "9600"},
        "DP9800": {"port": "COM1", "baud_rate": "9600"},
    }
    serial_port = SerialPortControl(
        devices,
        ("COM1", "COM5", "COM7"),
        ("600", "9600", "115200"),
    )
    window.setCentralWidget(serial_port)
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
