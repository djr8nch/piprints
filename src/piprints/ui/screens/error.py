"""Simple recovery presentation for application-level booth failures."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class ErrorScreen(QWidget):
    """Show a user-friendly error and provide a route back to idle."""

    def __init__(self, reset_session: Callable[[], None]) -> None:
        super().__init__()
        self._reset_session = reset_session
        self._message_label = QLabel("We couldn't prepare your photo.")
        self._message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_font = QFont()
        message_font.setPixelSize(32)
        message_font.setWeight(QFont.Weight.DemiBold)
        self._message_label.setFont(message_font)

        self._return_button = QPushButton("Return to start")
        self._return_button.setMinimumSize(360, 88)
        self._return_button.clicked.connect(self._reset_session)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(64, 48, 64, 48)
        layout.setSpacing(32)
        layout.addStretch()
        layout.addWidget(self._message_label)
        layout.addWidget(self._return_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()

        self.setStyleSheet("background-color: #151515; color: white;")

    def show_message(self, _message: str) -> None:
        """Keep failure feedback user-facing rather than technical."""
        self._message_label.setText("We couldn't prepare your photo.")
