"""Top-level window for the PiPrints basic booth workflow."""

from __future__ import annotations

from PySide6.QtGui import QCloseEvent, QShowEvent
from PySide6.QtWidgets import QMainWindow, QStackedWidget

from piprints.booth import BoothController, BoothState
from piprints.camera import Camera
from piprints.ui.event_bridge import QtEventBridge
from piprints.ui.screens.booth import BoothScreen
from piprints.ui.screens.home import HomeScreen


class MainWindow(QMainWindow):
    """Present the booth workflow's idle home and active capture screens."""

    def __init__(
        self,
        camera: Camera,
        booth: BoothController,
        event_bridge: QtEventBridge,
    ) -> None:
        super().__init__()
        self.setWindowTitle("PiPrints")
        self.resize(800, 480)
        self._booth_screen = BoothScreen(camera, booth, event_bridge)
        self._home_screen = HomeScreen(booth.begin_session)
        self._pages = QStackedWidget()
        self._pages.addWidget(self._home_screen)
        self._pages.addWidget(self._booth_screen)
        self.setCentralWidget(self._pages)
        event_bridge.state_changed.connect(self._present_state)
        self._present_state(BoothState.IDLE, booth.state)

    def showEvent(self, event: QShowEvent) -> None:
        """Start live preview if the current workflow state needs it."""
        super().showEvent(event)
        if self._pages.currentWidget() is self._booth_screen:
            self._booth_screen.start()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Stop booth workers before application shutdown releases the camera."""
        self._booth_screen.stop()
        super().closeEvent(event)

    def _present_state(self, _previous: BoothState, state: BoothState) -> None:
        """Navigate only in response to controller lifecycle transitions."""
        if state is BoothState.IDLE:
            self._booth_screen.stop()
            self._booth_screen.reset_presentation()
            self._home_screen.reset_presentation()
            self._pages.setCurrentWidget(self._home_screen)
            return

        self._pages.setCurrentWidget(self._booth_screen)
        if self.isVisible():
            self._booth_screen.start()
