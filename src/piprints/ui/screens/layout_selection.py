"""Touch-first selection of application-provided photo layouts."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from piprints.booth import LayoutOption


class LayoutSelectionScreen(QWidget):
    """Render application-provided layout options and forward one selection."""

    def __init__(
        self,
        options: Sequence[LayoutOption],
        select_layout: Callable[[str], object],
        cancel: Callable[[], None],
    ) -> None:
        super().__init__()
        self._select_layout = select_layout
        self._buttons: list[QPushButton] = []

        title = QLabel("Choose your layout")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 30px; font-weight: bold;")

        cards = QHBoxLayout()
        cards.setSpacing(16)
        for option in options:
            cards.addWidget(self._create_card(option), stretch=1)

        back_button = QPushButton("Back")
        back_button.setObjectName("layoutBackButton")
        back_button.setMinimumSize(180, 72)
        back_button.setStyleSheet("font-size: 24px; padding: 12px 32px;")
        back_button.clicked.connect(cancel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(16)
        layout.addWidget(title)
        layout.addLayout(cards, stretch=1)
        layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignLeft)

    def reset_presentation(self) -> None:
        """Re-enable cards after returning from this view without selection."""
        for button in self._buttons:
            button.setEnabled(True)
            button.clearFocus()

    def _create_card(self, option: LayoutOption) -> QPushButton:
        """Create one large card from a descriptor, not a composition strategy."""
        button = QPushButton()
        button.setObjectName(f"layoutCard_{option.identifier}")
        button.setMinimumHeight(260)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        button.setStyleSheet(
            "QPushButton { font-size: 22px; font-weight: bold; padding: 12px; }"
            "QPushButton:pressed { background-color: #b8b8b8; }"
            "QPushButton:disabled { color: #777777; background-color: #dddddd; }"
        )

        content = QVBoxLayout(button)
        content.setContentsMargins(12, 12, 12, 12)
        content.setSpacing(8)
        content.addWidget(self._preview(option), stretch=1)
        name = QLabel(option.name)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setWordWrap(True)
        name.setStyleSheet("font-size: 20px; font-weight: bold;")
        content.addWidget(name)
        detail = QLabel(option.description)
        detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detail.setStyleSheet("font-size: 17px;")
        content.addWidget(detail)
        button.clicked.connect(
            lambda _checked=False, identifier=option.identifier: self._select(
                identifier
            )
        )
        self._buttons.append(button)
        return button

    def _preview(self, option: LayoutOption) -> QWidget:
        """Draw a generic cell schematic from the descriptor's preview geometry."""
        preview = QWidget()
        grid = QGridLayout(preview)
        grid.setContentsMargins(12, 6, 12, 6)
        grid.setSpacing(5)
        for row in range(option.preview_rows):
            for column in range(option.preview_columns):
                cell = QLabel()
                cell.setMinimumSize(18, 18)
                cell.setStyleSheet(
                    "background-color: #dddddd; border: 2px solid #555555;"
                )
                grid.addWidget(cell, row, column)
        return preview

    def _select(self, identifier: str) -> None:
        """Disable all cards before issuing the controller-bound selection request."""
        for button in self._buttons:
            button.setEnabled(False)
        self._select_layout(identifier)
