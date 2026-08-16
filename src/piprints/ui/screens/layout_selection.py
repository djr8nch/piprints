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
from piprints.ui.styling.metrics import METRICS
from piprints.ui.styling.widgets import ButtonRole, apply_button_role


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
        title.setAccessibleName("Layout selection")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setProperty("styleRole", "screenTitle")

        cards = QHBoxLayout()
        cards.setSpacing(METRICS.spacing_medium)
        for option in options:
            cards.addWidget(self._create_card(option), stretch=1)

        back_button = QPushButton("Back")
        back_button.setObjectName("layoutBackButton")
        back_button.setAccessibleName("Back to home")
        back_button.setAccessibleDescription("Cancel layout selection and return home.")
        back_button.setMinimumSize(180, 72)
        apply_button_role(back_button, ButtonRole.QUIET)
        back_button.clicked.connect(cancel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 20, 28, 16)
        layout.setSpacing(METRICS.spacing_medium)
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
        button.setAccessibleName(f"Select {option.name} layout")
        button.setAccessibleDescription(option.description)
        button.setMinimumHeight(260)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        button.setCheckable(True)
        button.setProperty("selectionCard", True)

        content = QVBoxLayout(button)
        content.setContentsMargins(12, 12, 12, 12)
        content.setSpacing(8)
        content.addWidget(self._preview(option), stretch=1)
        name = QLabel(option.name)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setWordWrap(True)
        name.setProperty("styleRole", "screenTitle")
        content.addWidget(name)
        detail = QLabel(option.description)
        detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detail.setProperty("styleRole", "secondaryText")
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
                cell.setProperty("layoutPreviewCell", True)
                grid.addWidget(cell, row, column)
        return preview

    def _select(self, identifier: str) -> None:
        """Disable all cards before issuing the controller-bound selection request."""
        for button in self._buttons:
            button.setEnabled(False)
        self._select_layout(identifier)
