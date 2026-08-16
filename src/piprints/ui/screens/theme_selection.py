"""Touch-first selection of application-provided booth themes."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from piprints.themes import ThemeOption


class ThemeSelectionScreen(QWidget):
    """Render usable theme metadata and forward the user's selected identifier.

    This screen does not define or render themes. It only presents optional
    supplied preview files, so image composition remains outside the UI.
    """

    def __init__(
        self,
        options: Sequence[ThemeOption],
        select_theme: Callable[[str], object],
        cancel: Callable[[], None],
    ) -> None:
        super().__init__()
        self._select_theme = select_theme
        self._buttons: list[QPushButton] = []

        title = QLabel("Choose your theme")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 30px; font-weight: bold;")

        cards = QHBoxLayout()
        cards.setSpacing(16)
        cards.addStretch(1)
        for option in options:
            cards.addWidget(self._create_card(option), stretch=1)
        cards.addStretch(1)

        back_button = QPushButton("Back")
        back_button.setObjectName("themeBackButton")
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
        """Restore cards after a user returns without choosing a theme."""
        for button in self._buttons:
            button.setEnabled(True)
            button.clearFocus()

    def _create_card(self, option: ThemeOption) -> QPushButton:
        """Create one touch-sized card using only supplied metadata."""
        button = QPushButton()
        button.setObjectName(f"themeCard_{option.identifier}")
        button.setMinimumSize(300, 260)
        button.setMaximumWidth(480)
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
        name.setStyleSheet("font-size: 22px; font-weight: bold;")
        content.addWidget(name)
        button.clicked.connect(
            lambda _checked=False, identifier=option.identifier: self._select(
                identifier
            )
        )
        self._buttons.append(button)
        return button

    def _preview(self, option: ThemeOption) -> QLabel:
        """Return an optional supplied thumbnail without generating artwork."""
        preview = QLabel("Preview unavailable")
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview.setMinimumHeight(150)
        preview.setStyleSheet(
            "background-color: #dddddd; color: #555555; font-size: 18px;"
        )
        if option.preview_path is not None and option.preview_path.is_file():
            pixmap = QPixmap(str(option.preview_path))
            if not pixmap.isNull():
                preview.setText("")
                preview.setPixmap(
                    pixmap.scaled(
                        360,
                        150,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        return preview

    def _select(self, identifier: str) -> None:
        """Prevent double taps before forwarding the application request."""
        for button in self._buttons:
            button.setEnabled(False)
        self._select_theme(identifier)
