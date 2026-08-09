"""Integration tests for presenting PiPrints-owned preview frames in Qt."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from piprints.camera import PreviewFrame
from piprints.ui.widgets.camera_preview import CameraPreviewWidget
from tests.fakes import FakeCamera


def test_preview_widget_displays_and_resizes_a_frame() -> None:
    """The widget presents RGB data without camera-hardware dependencies.

    The private label assertion is retained because Qt exposes no useful public
    rendered-pixmap inspection API for this small widget.
    """
    application = QApplication.instance() or QApplication(["piprints"])
    widget = CameraPreviewWidget(FakeCamera())
    widget.resize(200, 100)
    widget.show()
    application.processEvents()

    widget.set_frame(PreviewFrame(b"\xff\x00\x00" * 4, 2, 2, 6))

    assert widget._image_label.pixmap() is not None
    assert widget._image_label.pixmap().size().width() <= 200

    widget.close()
