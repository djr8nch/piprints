"""Regression coverage for production touchscreen accessibility and screen fit."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PySide6.QtWidgets import QApplication, QPushButton

from piprints.booth import (
    BoothController,
    BoothEvent,
    BoothEventType,
    BoothState,
    Countdown,
)
from piprints.bootstrap import create_layout_catalog, create_theme_catalog
from piprints.imaging import Photo, PhotoLoader, PhotoPipeline
from piprints.imaging.layouts import FourPhotoLayout
from piprints.storage import FilesystemPhotoStorage
from piprints.ui import QtEventBridge
from piprints.ui.screens.main_window import MainWindow
from tests.fakes import FakeCamera


def make_window(tmp_path: Path) -> tuple[MainWindow, BoothController, QtEventBridge]:
    """Create every production screen with no physical hardware dependency."""
    bridge = QtEventBridge()
    controller = BoothController(
        camera=FakeCamera(),
        capture_directory=tmp_path / "captures",
        photo_loader=PhotoLoader(),
        photo_pipeline=PhotoPipeline(),
        layout=FourPhotoLayout(),
        layout_catalog=create_layout_catalog(),
        theme_catalog=create_theme_catalog(),
        photo_storage=FilesystemPhotoStorage(tmp_path / "photos"),
        countdown=Countdown(3, delay=lambda _: None),
        listeners=[bridge],
    )
    return MainWindow(FakeCamera(), controller, bridge), controller, bridge


def assert_visible_controls_fit(screen: object) -> None:
    """Assert visible buttons remain inside their 800 by 480 parent screen."""
    for button in screen.findChildren(QPushButton):  # type: ignore[attr-defined]
        if button.isVisible():
            assert screen.rect().contains(button.geometry())  # type: ignore[attr-defined]


def test_production_screens_fit_at_800_by_480_and_expose_accessible_controls(
    tmp_path: Path,
) -> None:
    """Every customer-facing state has touch controls within the target viewport."""
    application = QApplication.instance() or QApplication(["piprints"])
    window, _controller, bridge = make_window(tmp_path)
    window.resize(800, 480)
    window.show()
    application.processEvents()

    assert window.size().toTuple() == (800, 480)
    assert window._home_screen._start_button.minimumHeight() >= 88
    assert window._home_screen._start_button.accessibleName() == (
        "Start a photo booth session"
    )
    assert_visible_controls_fit(window._home_screen)

    window._home_screen._start_button.click()
    application.processEvents()
    assert_visible_controls_fit(window._layout_selection_screen)
    assert all(
        button.accessibleName()
        for button in window._layout_selection_screen._buttons
    )

    window._layout_selection_screen._buttons[0].click()
    application.processEvents()
    assert_visible_controls_fit(window._theme_selection_screen)
    assert all(
        button.accessibleName()
        for button in window._theme_selection_screen._buttons
    )

    window._theme_selection_screen._buttons[0].click()
    application.processEvents()
    booth = window._booth_screen
    assert booth._take_photo_button.minimumHeight() >= 88
    assert booth._take_photo_button.accessibleName() == "Take photo"
    assert_visible_controls_fit(booth)

    bridge.on_booth_event(
        BoothEvent(
            event_type=BoothEventType.STATE_CHANGED,
            previous_state=BoothState.CAPTURING,
            state=BoothState.PROCESSING,
        )
    )
    application.processEvents()
    assert booth._processing_presentation._indicator.accessibleName() == (
        "Photo processing in progress"
    )

    booth._show_review(Photo(Image.new("RGB", (240, 120), "blue")))
    application.processEvents()
    assert booth._review_label.height() > booth.height() // 2
    assert booth._retake_button.minimumHeight() >= 76
    assert booth._done_button.minimumHeight() >= 76
    assert_visible_controls_fit(booth)

    bridge.on_booth_event(
        BoothEvent(
            event_type=BoothEventType.ERROR,
            state=BoothState.ERROR,
        )
    )
    application.processEvents()
    assert window._error_screen._return_button.minimumHeight() >= 88
    assert_visible_controls_fit(window._error_screen)

    window.close()
    application.processEvents()


def test_returning_home_clears_stale_photo_status_and_error_copy(
    tmp_path: Path,
) -> None:
    """A subsequent customer never sees the previous session's private state."""
    application = QApplication.instance() or QApplication(["piprints"])
    window, _controller, bridge = make_window(tmp_path)
    booth = window._booth_screen
    booth._show_review(Photo(Image.new("RGB", (20, 10), "blue")))
    booth._save_status_label.setText("✓ Saved")
    booth._print_status_label.setText("✓ Printed")
    bridge.on_booth_event(
        BoothEvent(
            event_type=BoothEventType.ERROR,
            state=BoothState.ERROR,
        )
    )

    window._present_state(BoothState.ERROR, BoothState.IDLE)

    assert booth._review_pixmap is None
    assert booth._save_status_label.text() == ""
    assert booth._print_status_label.text() == "Printer unavailable"
    assert window._error_screen._message_label.text() == ""
    assert window._pages.currentWidget() is window._home_screen

    window.close()
    application.processEvents()
