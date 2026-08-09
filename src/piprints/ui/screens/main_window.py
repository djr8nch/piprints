"""Top-level window for the PiPrints application shell."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow


class MainWindow(QMainWindow):
    """Display the initial PiPrints application shell."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PiPrints")
        self.resize(800, 480)

        placeholder = QLabel("PiPrints\nApplication shell")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(placeholder)
