"""Focused contracts for the shared default PiPrints visual identity."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from piprints.bootstrap import create_application
from piprints.ui.styling import PALETTE, default_stylesheet, logo_path
from piprints.ui.styling.widgets import (
    ButtonRole,
    StatusRole,
    apply_button_role,
    set_status,
)


def test_default_stylesheet_exposes_semantic_brand_tokens() -> None:
    """The default identity retains the supplied brand colors and UI states."""
    stylesheet = default_stylesheet()

    assert PALETTE.brand_pink in stylesheet
    assert PALETTE.brand_mint in stylesheet
    assert 'styleRole="primary"' in stylesheet
    assert 'styleRole="accent"' in stylesheet
    assert 'statusRole="success"' in stylesheet
    assert 'statusRole="error"' in stylesheet
    assert ":disabled" in stylesheet
    assert ":checked" in stylesheet


def test_runtime_logo_is_packaged_outside_documentation_assets() -> None:
    """Qt runtime branding resolves from the UI package, not docs/assets."""
    path = logo_path()

    assert path.is_file()
    assert "docs" not in path.parts
    assert path.name == "logo.png"


def test_shared_semantic_helpers_assign_qt_properties() -> None:
    """Screens can use common states without embedding independent QSS."""
    application = QApplication.instance() or QApplication(["piprints"])
    button = QPushButton("Continue")
    from PySide6.QtWidgets import QLabel

    status = QLabel()
    apply_button_role(button, ButtonRole.PRIMARY)
    set_status(status, "✓ Saved", StatusRole.SUCCESS)

    assert button.property("styleRole") == "primary"
    assert status.text() == "✓ Saved"
    assert status.property("statusRole") == "success"
    application.processEvents()


def test_application_factory_applies_the_default_stylesheet() -> None:
    """Normal startup applies one presentation-wide stylesheet."""
    application = create_application(["piprints"])

    assert PALETTE.brand_mint in application.styleSheet()
