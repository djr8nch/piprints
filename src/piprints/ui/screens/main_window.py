"""Top-level window for the PiPrints live camera preview."""

from __future__ import annotations

from PySide6.QtGui import QCloseEvent, QShowEvent
from PySide6.QtWidgets import QMainWindow

from piprints.camera import Camera
from piprints.ui.widgets.camera_preview import CameraPreviewWidget


class MainWindow(QMainWindow):
    """Display the PiPrints live camera preview."""

    def __init__(self, camera: Camera) -> None:
        super().__init__()
        self.setWindowTitle("PiPrints Camera Preview")
        self.resize(800, 480)
        self._preview = CameraPreviewWidget(camera)
        self.setCentralWidget(self._preview)

    def showEvent(self, event: QShowEvent) -> None:
        """Start delivering frames once the preview window is visible."""
        super().showEvent(event)
        self._preview.start()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Stop frame delivery before application shutdown releases the camera."""
        self._preview.stop()
        super().closeEvent(event)
