"""Integration tests for the touch-first idle home presentation."""

from __future__ import annotations

import os
from inspect import getsource
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from piprints.booth import BoothController, BoothState, Countdown
from piprints.bootstrap import create_layout_catalog
from piprints.imaging import PhotoLoader, PhotoPipeline
from piprints.imaging.layouts import FourPhotoLayout
from piprints.storage import FilesystemPhotoStorage
from piprints.ui import QtEventBridge
from piprints.ui.screens.home import HomeScreen
from piprints.ui.screens.main_window import MainWindow
from tests.fakes import FakeCamera


def make_controller(capture_directory: Path) -> BoothController:
    """Create a one-photo controller suitable for presentation transitions."""
    return BoothController(
        camera=FakeCamera(),
        capture_directory=capture_directory,
        photo_loader=PhotoLoader(),
        photo_pipeline=PhotoPipeline(),
        layout=FourPhotoLayout(),
        photo_storage=FilesystemPhotoStorage(capture_directory.parent / "photos"),
        countdown=Countdown(3, delay=lambda _: None),
        layout_catalog=create_layout_catalog(),
    )


def test_idle_window_displays_a_touch_sized_home_screen_at_800_by_480(
    tmp_path: Path,
) -> None:
    """The production display size keeps the sole home action fully visible."""
    application = QApplication.instance() or QApplication(["piprints"])
    controller = make_controller(tmp_path / "captures")
    event_bridge = QtEventBridge()
    controller.add_event_listener(event_bridge)
    window = MainWindow(FakeCamera(), controller, event_bridge)
    window.resize(800, 480)
    window.show()
    application.processEvents()

    home = window._home_screen
    button = home._start_button

    assert controller.state is BoothState.IDLE
    assert window._pages.currentWidget() is home
    assert button.minimumWidth() >= 360
    assert button.minimumHeight() >= 104
    assert button.geometry().intersects(home.rect())
    assert home.rect().contains(button.geometry())

    window.close()
    application.processEvents()


def test_start_opens_layout_selection_once(
    tmp_path: Path,
) -> None:
    """Repeated home taps cannot create a session before layout selection."""
    application = QApplication.instance() or QApplication(["piprints"])
    controller = make_controller(tmp_path / "captures")
    event_bridge = QtEventBridge()
    controller.add_event_listener(event_bridge)
    window = MainWindow(FakeCamera(), controller, event_bridge)

    window._home_screen._start_button.click()
    window._home_screen._start_button.click()

    assert controller.state is BoothState.IDLE
    assert controller.session is None
    assert window._pages.currentWidget() is window._layout_selection_screen
    assert not window._home_screen._start_button.isEnabled()

    window.close()
    application.processEvents()


def test_returning_to_idle_restores_a_clean_home_presentation(tmp_path: Path) -> None:
    """A completed session leaves no prior session details on the home screen."""
    application = QApplication.instance() or QApplication(["piprints"])
    controller = make_controller(tmp_path / "captures")
    event_bridge = QtEventBridge()
    controller.add_event_listener(event_bridge)
    window = MainWindow(FakeCamera(), controller, event_bridge)

    window._home_screen._start_button.click()
    window._layout_selection_screen._buttons[0].click()
    controller.start_countdown()
    controller.run_countdown()
    controller.capture()
    controller.complete_session()
    controller.finish_session()

    assert controller.state is BoothState.IDLE
    assert window._pages.currentWidget() is window._home_screen
    assert window._home_screen._start_button.isEnabled()
    assert window._booth_screen._review_label.text() == ""
    assert window._booth_screen._countdown_label.text() == ""
    assert window._booth_screen._progress_label.text() == ""

    window.close()
    application.processEvents()


def test_home_screen_has_no_hardware_dependency() -> None:
    """The idle widget only invokes its injected application action."""
    application = QApplication.instance() or QApplication(["piprints"])
    requests: list[str] = []
    screen = HomeScreen(lambda: requests.append("begin"))

    screen._start_button.click()
    screen._start_button.click()

    assert requests == ["begin"]
    assert not screen._start_button.isEnabled()
    source = getsource(HomeScreen)
    assert "camera" not in source.lower()
    assert "BoothController" not in source
    application.processEvents()
