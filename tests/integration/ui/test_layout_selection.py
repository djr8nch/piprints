"""Integration tests for touch-first layout selection presentation."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from piprints.booth import BoothController, BoothState, Countdown
from piprints.bootstrap import create_layout_catalog
from piprints.imaging import PhotoLoader, PhotoPipeline
from piprints.imaging.layouts import FourPhotoLayout
from piprints.storage import FilesystemPhotoStorage
from piprints.ui import QtEventBridge
from piprints.ui.screens.main_window import MainWindow
from tests.fakes import FakeCamera


def make_window(tmp_path: Path) -> tuple[MainWindow, BoothController]:
    """Create the production catalog wired through a fake-backed controller."""
    controller = BoothController(
        camera=FakeCamera(),
        capture_directory=tmp_path / "captures",
        photo_loader=PhotoLoader(),
        photo_pipeline=PhotoPipeline(),
        layout=FourPhotoLayout(),
        layout_catalog=create_layout_catalog(),
        photo_storage=FilesystemPhotoStorage(tmp_path / "photos"),
        countdown=Countdown(3, delay=lambda _: None),
    )
    bridge = QtEventBridge()
    controller.add_event_listener(bridge)
    return MainWindow(FakeCamera(), controller, bridge), controller


def test_currently_supported_layouts_fit_as_three_cards_at_800_by_480(
    tmp_path: Path,
) -> None:
    """Only catalog-backed layouts appear, with no scrollable selection flow."""
    application = QApplication.instance() or QApplication(["piprints"])
    window, controller = make_window(tmp_path)
    window.resize(800, 480)
    window.show()
    window._home_screen._start_button.click()
    application.processEvents()

    screen = window._layout_selection_screen
    identifiers = [button.objectName() for button in screen._buttons]

    assert identifiers == ["layoutCard_single", "layoutCard_grid", "layoutCard_strip"]
    assert "layoutCard_theme" not in identifiers
    assert controller.state is BoothState.IDLE
    assert len(screen._buttons) == 3
    assert all(screen.rect().contains(button.geometry()) for button in screen._buttons)
    assert all(button.minimumHeight() >= 260 for button in screen._buttons)

    window.close()
    application.processEvents()


def test_selecting_a_layout_starts_the_matching_session_once(tmp_path: Path) -> None:
    """A card selection records its ID and capture count in the workflow session."""
    application = QApplication.instance() or QApplication(["piprints"])
    window, controller = make_window(tmp_path)

    window._home_screen._start_button.click()
    strip_card = window._layout_selection_screen._buttons[2]
    strip_card.click()
    session = controller.session
    strip_card.click()

    assert controller.state is BoothState.PREPARING
    assert controller.session is session
    assert session is not None
    assert session.layout_identifier == "strip"
    assert session.target_photo_count == 4
    assert window._pages.currentWidget() is window._booth_screen
    assert all(
        not button.isEnabled() for button in window._layout_selection_screen._buttons
    )

    window.close()
    application.processEvents()


def test_back_from_layout_selection_returns_to_valid_idle_home(tmp_path: Path) -> None:
    """Canceling selection leaves the controller without an active session."""
    application = QApplication.instance() or QApplication(["piprints"])
    window, controller = make_window(tmp_path)

    window._home_screen._start_button.click()
    back_button = window._layout_selection_screen.findChild(
        QPushButton, "layoutBackButton"
    )
    assert back_button is not None
    back_button.click()

    assert controller.state is BoothState.IDLE
    assert controller.session is None
    assert window._pages.currentWidget() is window._home_screen
    assert window._home_screen._start_button.isEnabled()

    window.close()
    application.processEvents()
