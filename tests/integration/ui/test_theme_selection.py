"""Integration tests for touch-first theme selection presentation."""

from __future__ import annotations

import os
from inspect import getsource
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from piprints.booth import BoothController, BoothState, Countdown
from piprints.bootstrap import create_layout_catalog
from piprints.imaging import PhotoLoader, PhotoPipeline
from piprints.imaging.layouts import FourPhotoLayout
from piprints.storage import FilesystemPhotoStorage
from piprints.themes import ThemeCatalog, ThemeOption
from piprints.ui import QtEventBridge
from piprints.ui.screens.main_window import MainWindow
from piprints.ui.screens.theme_selection import ThemeSelectionScreen
from tests.fakes import FakeCamera


def make_window(
    tmp_path: Path, theme_catalog: ThemeCatalog | None = None
) -> tuple[MainWindow, BoothController]:
    """Create the selection flow with a configurable metadata catalog."""
    controller = BoothController(
        camera=FakeCamera(),
        capture_directory=tmp_path / "captures",
        photo_loader=PhotoLoader(),
        photo_pipeline=PhotoPipeline(),
        layout=FourPhotoLayout(),
        layout_catalog=create_layout_catalog(),
        theme_catalog=theme_catalog,
        photo_storage=FilesystemPhotoStorage(tmp_path / "photos"),
        countdown=Countdown(3, delay=lambda _: None),
    )
    bridge = QtEventBridge()
    controller.add_event_listener(bridge)
    return MainWindow(FakeCamera(), controller, bridge), controller


def open_theme_selection(window: MainWindow) -> None:
    """Navigate through the required layout selection before theme choice."""
    window._home_screen._start_button.click()
    window._layout_selection_screen._buttons[0].click()


def test_usable_themes_fit_as_large_cards_at_800_by_480(tmp_path: Path) -> None:
    """Only catalog-exposed usable options appear without scrolling."""
    application = QApplication.instance() or QApplication(["piprints"])
    catalog = ThemeCatalog(
        (
            ThemeOption("classic", "Classic"),
            ThemeOption("party", "Party"),
            ThemeOption("retired", "Retired", available=False),
        )
    )
    window, controller = make_window(tmp_path, catalog)
    window.resize(800, 480)
    window.show()
    open_theme_selection(window)
    application.processEvents()

    screen = window._theme_selection_screen
    assert [button.objectName() for button in screen._buttons] == [
        "themeCard_classic",
        "themeCard_party",
    ]
    assert screen.findChild(QPushButton, "themeCard_retired") is None
    assert controller.state is BoothState.IDLE
    assert all(screen.rect().contains(button.geometry()) for button in screen._buttons)
    assert all(button.minimumHeight() >= 260 for button in screen._buttons)

    window.close()
    application.processEvents()


def test_theme_selection_invokes_controller_and_persists_in_session(
    tmp_path: Path,
) -> None:
    """The selected metadata identifier crosses the UI/application boundary."""
    application = QApplication.instance() or QApplication(["piprints"])
    catalog = ThemeCatalog((ThemeOption("classic", "Classic"),))
    window, controller = make_window(tmp_path, catalog)

    open_theme_selection(window)
    window._theme_selection_screen._buttons[0].click()

    assert controller.state is BoothState.PREPARING
    assert controller.session is not None
    assert controller.session.layout_identifier == "single"
    assert controller.session.theme_identifier == "classic"
    assert window._pages.currentWidget() is window._booth_screen

    window.close()
    application.processEvents()


def test_back_from_theme_selection_preserves_idle_session_lifecycle(
    tmp_path: Path,
) -> None:
    """Returning to layouts before a choice creates no partial session."""
    application = QApplication.instance() or QApplication(["piprints"])
    window, controller = make_window(tmp_path)

    open_theme_selection(window)
    back_button = window._theme_selection_screen.findChild(
        QPushButton, "themeBackButton"
    )
    assert back_button is not None
    back_button.click()

    assert controller.state is BoothState.IDLE
    assert controller.session is None
    assert window._pages.currentWidget() is window._layout_selection_screen

    window.close()
    application.processEvents()


def test_theme_selection_remains_metadata_presentation_only() -> None:
    """Theme choice must not acquire image composition responsibilities."""
    source = getsource(ThemeSelectionScreen)

    assert "piprints.imaging" not in source
    assert ".compose(" not in source
