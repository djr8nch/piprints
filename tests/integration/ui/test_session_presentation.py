"""Integration tests for multi-photo session presentation at the Qt boundary."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PySide6.QtWidgets import QApplication

from piprints.booth import BoothController, Countdown
from piprints.imaging import Photo, PhotoLoader, PhotoPipeline
from piprints.imaging.layouts import FourPhotoLayout
from piprints.storage import FilesystemPhotoStorage
from piprints.ui.photo_presentation import photo_to_pixmap
from piprints.ui.screens.booth import BoothScreen
from tests.fakes import FakeCamera


def make_controller(capture_directory: Path) -> BoothController:
    """Create a hardware-independent controller using the standard grid layout."""
    return BoothController(
        camera=FakeCamera(),
        capture_directory=capture_directory,
        photo_loader=PhotoLoader(),
        photo_pipeline=PhotoPipeline(),
        layout=FourPhotoLayout(),
        photo_storage=FilesystemPhotoStorage(capture_directory.parent / "photos"),
        countdown=Countdown(3, delay=lambda _: None),
    )


def test_screen_progress_reads_the_controller_capture_session(tmp_path: Path) -> None:
    """Starting a session displays its first capture position without UI state."""
    application = QApplication.instance() or QApplication(["piprints"])
    controller = make_controller(tmp_path / "captures")
    screen = BoothScreen(FakeCamera(), controller)

    screen._take_photo_button.click()

    assert screen._progress_label.text() == "Photo 1 of 4"

    screen.stop()
    screen.close()
    application.processEvents()


def test_layout_photo_converts_to_a_displayable_qt_pixmap() -> None:
    """The UI previews the composed Photo rather than recalculating its layout."""
    application = QApplication.instance() or QApplication(["piprints"])
    layout = FourPhotoLayout(canvas_width=44, canvas_height=44, margin=2, gutter=2)
    photos = [Photo(Image.new("RGB", (38, 38), color)) for color in ("red",) * 4]

    pixmap = photo_to_pixmap(layout.compose(photos))

    assert not pixmap.isNull()
    assert pixmap.size().toTuple() == (44, 44)
    application.processEvents()
