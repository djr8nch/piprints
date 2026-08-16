"""Application-wide QSS for the default PiPrints presentation."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

from piprints.ui.styling.metrics import METRICS
from piprints.ui.styling.palette import PALETTE


def default_stylesheet() -> str:
    """Return the compact shared stylesheet for the current PiPrints brand."""
    p = PALETTE
    m = METRICS
    return f"""
        QMainWindow, QWidget {{
            background-color: {p.background};
            color: {p.text_primary};
            font-size: {m.body_text_size}px;
        }}
        QLabel[styleRole="screenTitle"] {{
            font-size: {m.title_text_size}px;
            font-weight: 700;
            color: {p.text_primary};
        }}
        QLabel[styleRole="heroTitle"] {{
            font-size: {m.hero_text_size}px;
            font-weight: 700;
            color: {p.text_primary};
        }}
        QLabel[styleRole="secondaryText"] {{ color: {p.text_secondary}; }}
        QPushButton {{
            background-color: {p.surface};
            border: 2px solid {p.border};
            border-radius: {m.corner_radius}px;
            color: {p.text_primary};
            font-size: 22px;
            font-weight: 700;
            padding: 8px 20px;
        }}
        QPushButton:pressed {{ background-color: {p.surface_subtle}; }}
        QPushButton:disabled {{
            background-color: {p.disabled_surface};
            border-color: {p.disabled_surface};
            color: {p.disabled_text};
        }}
        QPushButton:focus {{ border: 3px solid {p.focus}; }}
        QPushButton[styleRole="primary"] {{
            background-color: {p.brand_mint};
            border-color: {p.focus};
        }}
        QPushButton[styleRole="primary"]:pressed {{
            background-color: {p.pressed_mint};
        }}
        QPushButton[styleRole="accent"] {{
            background-color: {p.brand_pink};
            border-color: {p.accent_border};
        }}
        QPushButton[styleRole="accent"]:pressed {{
            background-color: {p.pressed_pink};
        }}
        QPushButton[styleRole="quiet"] {{
            background-color: transparent;
            border-color: transparent;
            color: {p.text_secondary};
        }}
        QPushButton[styleRole="error"] {{
            background-color: {p.error_surface};
            border-color: {p.error_border};
            color: {p.error_text};
        }}
        QPushButton[selectionCard="true"] {{
            background-color: {p.surface};
            border: 2px solid {p.border};
            border-radius: {m.corner_radius}px;
            padding: 10px;
        }}
        QPushButton[selectionCard="true"]:checked {{
            background-color: {p.brand_pink};
            border: 4px solid {p.focus};
        }}
        QPushButton[selectionCard="true"]:pressed {{
            background-color: {p.pressed_pink};
        }}
        QLabel[statusRole="success"] {{
            background-color: {p.success_surface};
            border-radius: 8px;
            color: {p.success_text};
            font-weight: 700;
            padding: 3px 8px;
        }}
        QLabel[statusRole="error"] {{
            background-color: {p.error_surface};
            border: 1px solid {p.error_border};
            border-radius: 8px;
            color: {p.error_text};
            font-weight: 700;
            padding: 3px 8px;
        }}
        QLabel[statusRole="neutral"] {{ color: {p.text_secondary}; }}
        QLabel[preview="true"] {{
            background-color: {p.preview_background};
            color: white;
        }}
        QLabel[previewPlaceholder="true"] {{
            background-color: {p.surface_subtle};
            border-radius: 8px;
            color: {p.text_secondary};
        }}
        QLabel[layoutPreviewCell="true"] {{
            background-color: {p.brand_mint};
            border: 2px solid {p.focus};
            border-radius: 4px;
        }}
        QWidget[countdownOverlay="true"] {{ background-color: {p.overlay}; }}
        QLabel[countdown="true"] {{
            color: white;
            font-size: 240px;
            font-weight: 700;
        }}
        QWidget#processingPresentation {{
            background-color: {p.surface};
        }}
        QWidget#processingPresentation QProgressBar {{
            background-color: {p.surface_subtle};
            border: 1px solid {p.border};
            border-radius: 8px;
        }}
        QWidget#processingPresentation QProgressBar::chunk {{
            background-color: {p.brand_mint};
            border-radius: 7px;
        }}
        QWidget#errorScreen {{
            background-color: {p.error_surface};
        }}
        QWidget#errorScreen QLabel[styleRole="screenTitle"] {{ color: {p.error_text}; }}
    """


def apply_default_style(application: QApplication) -> None:
    """Apply the current default PiPrints visual identity to one Qt app."""
    application.setStyleSheet(default_stylesheet())
