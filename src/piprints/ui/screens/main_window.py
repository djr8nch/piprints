"""Top-level window for the PiPrints basic booth workflow."""

from __future__ import annotations

from PySide6.QtGui import QCloseEvent, QShowEvent
from PySide6.QtWidgets import QMainWindow

from piprints.booth import BoothController
from piprints.camera import Camera
from piprints.ui.screens.booth import BoothScreen


class MainWindow(QMainWindow):
    """Display the initial PiPrints booth capture workflow."""

    def __init__(self, camera: Camera, booth: BoothController) -> None:
        super().__init__()
        self.setWindowTitle("PiPrints")
        self.resize(800, 480)
        self._booth_screen = BoothScreen(camera, booth)
        self.setCentralWidget(self._booth_screen)

    def showEvent(self, event: QShowEvent) -> None:
        """Start live preview once the window is visible."""
        super().showEvent(event)
        self._booth_screen.start()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Stop booth workers before application shutdown releases the camera."""
        self._booth_screen.stop()
        super().closeEvent(event)
