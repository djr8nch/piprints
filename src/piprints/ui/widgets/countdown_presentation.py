"""Focused Qt presentation for application-owned booth countdown ticks."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class CountdownPresentation(QWidget):
    """Show one large countdown value over the active booth presentation.

    This widget intentionally owns no timer. Its value is updated solely by
    the Qt bridge's delivery of countdown events emitted by the booth
    workflow.
    """

    def __init__(self) -> None:
        super().__init__()
        self._number_label = QLabel()
        self._number_label.setObjectName("countdownNumber")
        self._number_label.setAccessibleName("Countdown to photo")
        self._number_label.setAccessibleDescription(
            "The number of seconds before PiPrints takes the next photo."
        )
        self._number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        number_font = QFont()
        number_font.setPixelSize(240)
        number_font.setWeight(QFont.Weight.Bold)
        self._number_label.setFont(number_font)
        self._number_label.setProperty("countdown", True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._number_label)

        self.setProperty("countdownOverlay", True)
        self.hide()

    @property
    def value(self) -> int | None:
        """Return the currently displayed application countdown value."""
        text = self._number_label.text()
        return int(text) if text else None

    def show_tick(self, value: int) -> None:
        """Present a validated display value supplied by the booth workflow."""
        self._number_label.setText(str(value))
        self.show()
        self.raise_()

    def begin(self) -> None:
        """Show a clean overlay as the workflow enters countdown state."""
        self._number_label.clear()
        self.show()
        self.raise_()

    def clear(self) -> None:
        """Hide the presentation and discard any value from a prior session."""
        self._number_label.clear()
        self.hide()
