"""Tests for presenting PiPrints-owned preview frames in Qt."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from piprints.camera import Camera, PreviewFrame
from piprints.ui.widgets.camera_preview import CameraPreviewWidget


class FakeCamera(Camera):
    """A camera fake that is not used when testing direct frame presentation."""

    def start(self) -> None:
        """Start the fake camera."""

    def capture(self, destination: Path) -> Path:
        """Capture is outside this test's scope."""
        return destination

    def capture_preview_frame(self) -> PreviewFrame:
        """Return a single RGB pixel."""
        return PreviewFrame(b"\x00\x00\x00", 1, 1, 3)

    def stop(self) -> None:
        """Stop the fake camera."""


def test_preview_widget_displays_and_resizes_a_frame() -> None:
    """The widget accepts RGB data without camera-hardware dependencies."""
    application = QApplication.instance() or QApplication(["piprints"])
    widget = CameraPreviewWidget(FakeCamera())
    widget.resize(200, 100)
    widget.show()
    application.processEvents()

    widget.set_frame(PreviewFrame(b"\xff\x00\x00" * 4, 2, 2, 6))

    assert application is not None
    assert widget._image_label.pixmap() is not None
    assert widget._image_label.pixmap().size().width() <= 200

    widget.close()
