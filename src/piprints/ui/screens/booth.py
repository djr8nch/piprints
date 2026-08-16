"""Minimal PySide6 presentation for the basic booth capture workflow."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QResizeEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStackedLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from piprints.booth import (
    BoothCaptureError,
    BoothController,
    BoothState,
)
from piprints.camera import Camera
from piprints.imaging import Photo
from piprints.ui.event_bridge import QtEventBridge
from piprints.ui.photo_presentation import photo_to_pixmap
from piprints.ui.widgets.camera_preview import CameraPreviewWidget
from piprints.ui.widgets.countdown_presentation import CountdownPresentation
from piprints.ui.widgets.processing_presentation import ProcessingPresentation

logger = logging.getLogger(__name__)


class _CaptureWorker(QThread):
    """Run the blocking booth capture operation away from the UI thread."""

    capture_succeeded = Signal(object)
    capture_failed = Signal(str)

    def __init__(self, controller: BoothController) -> None:
        super().__init__()
        self._controller = controller

    def run(self) -> None:
        """Capture the photo and notify the UI with a simple result."""
        try:
            self.capture_succeeded.emit(self._controller.capture())
        except BoothCaptureError as error:
            logger.exception("Booth capture worker failed")
            self.capture_failed.emit(str(error))


class _CountdownWorker(QThread):
    """Execute application-owned countdown timing away from the UI thread."""

    countdown_failed = Signal(str)

    def __init__(self, controller: BoothController) -> None:
        super().__init__()
        self._controller = controller

    def run(self) -> None:
        """Execute the controller-owned countdown lifecycle."""
        try:
            self._controller.run_countdown()
        except Exception as error:
            logger.exception("Booth countdown worker failed")
            self.countdown_failed.emit(str(error))


class _CompletionWorker(QThread):
    """Persist a reviewed session without delaying Qt event handling."""

    completion_failed = Signal(str)

    def __init__(self, controller: BoothController) -> None:
        super().__init__()
        self._controller = controller

    def run(self) -> None:
        """Complete and finish the controller lifecycle for the reviewed photo."""
        try:
            self._controller.complete_session()
            self._controller.finish_session()
        except Exception as error:
            logger.exception("Booth session completion failed")
            self.completion_failed.emit(str(error))


class BoothScreen(QWidget):
    """Render session workflow state and forward intent to the controller."""

    def __init__(
        self,
        camera: Camera,
        controller: BoothController,
        event_bridge: QtEventBridge,
    ) -> None:
        super().__init__()
        self._controller = controller
        self._capture_worker: _CaptureWorker | None = None
        self._countdown_worker: _CountdownWorker | None = None
        self._completion_worker: _CompletionWorker | None = None
        self._review_pixmap: QPixmap | None = None
        self._is_stopping = False
        self._event_bridge = event_bridge
        self._event_bridge.countdown_tick.connect(self._show_countdown_tick)
        self._event_bridge.state_changed.connect(self._present_booth_state)
        self._event_bridge.review_ready.connect(self._show_review)

        self._preview = CameraPreviewWidget(camera)
        self._countdown_presentation = CountdownPresentation()
        # Retain this alias while the existing screen tests inspect the label.
        self._countdown_label = self._countdown_presentation._number_label
        self._progress_label = QLabel()
        self._progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._take_photo_button = QPushButton("Take Photo")
        self._take_photo_button.clicked.connect(self._start_countdown)

        preview_content = QWidget()
        preview_layout = QVBoxLayout(preview_content)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.addWidget(self._preview, stretch=1)
        preview_layout.addWidget(self._progress_label)
        preview_layout.addWidget(self._take_photo_button)

        preview_page = QWidget()
        preview_stack = QStackedLayout(preview_page)
        preview_stack.setStackingMode(QStackedLayout.StackingMode.StackAll)
        preview_stack.addWidget(preview_content)
        preview_stack.addWidget(self._countdown_presentation)

        self._review_label = QLabel()
        self._review_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._review_label.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored
        )
        self._review_label.setStyleSheet("background-color: black;")
        self._review_status_label = QLabel("Your photo is ready")
        self._review_status_label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        )
        self._review_status_label.setStyleSheet("font-size: 20px;")
        self._retake_button = QPushButton("Retake")
        self._retake_button.clicked.connect(self._retake)
        self._retake_button.setMinimumSize(128, 72)
        self._done_button = QPushButton("Done")
        self._done_button.setMinimumSize(220, 72)
        self._done_button.setStyleSheet("font-size: 28px; font-weight: bold;")
        self._done_button.clicked.connect(self._finish_review)

        review_actions = QWidget()
        review_actions.setMinimumHeight(88)
        actions_layout = QHBoxLayout(review_actions)
        actions_layout.setContentsMargins(20, 8, 20, 8)
        actions_layout.setSpacing(12)
        actions_layout.addWidget(self._review_status_label, stretch=1)
        actions_layout.addWidget(self._retake_button)
        actions_layout.addWidget(self._done_button)

        review_page = QWidget()
        review_layout = QVBoxLayout(review_page)
        review_layout.setContentsMargins(0, 0, 0, 0)
        review_layout.addWidget(self._review_label, stretch=1)
        review_layout.addWidget(review_actions)

        self._processing_presentation = ProcessingPresentation()

        self._pages = QStackedWidget()
        self._pages.addWidget(preview_page)
        self._pages.addWidget(review_page)
        self._pages.addWidget(self._processing_presentation)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._pages)

        self._update_progress()

    def start(self) -> None:
        """Start live preview when the window becomes visible."""
        self._is_stopping = False
        self._preview.start()

    def stop(self) -> None:
        """Stop timers and workers before the application releases the camera."""
        self._is_stopping = True
        self._preview.stop()
        if self._countdown_worker is not None and self._countdown_worker.isRunning():
            if not self._countdown_worker.wait(5000):
                logger.warning(
                    "Booth countdown worker did not stop within five seconds"
                )
        if self._capture_worker is not None and self._capture_worker.isRunning():
            if not self._capture_worker.wait(5000):
                logger.warning("Booth capture worker did not stop within five seconds")
        if self._completion_worker is not None and self._completion_worker.isRunning():
            if not self._completion_worker.wait(5000):
                logger.warning(
                    "Booth completion worker did not stop within five seconds"
                )

    def reset_presentation(self) -> None:
        """Clear session-specific presentation before the next idle screen."""
        self._clear_review_presentation()
        self._countdown_presentation.clear()
        self._progress_label.clear()
        self._take_photo_button.setEnabled(True)
        self._pages.setCurrentIndex(0)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Scale the reviewed photo as the window size changes."""
        self._update_review_pixmap()
        super().resizeEvent(event)

    def _start_countdown(self) -> None:
        """Begin the application-owned countdown without blocking Qt's UI thread."""
        self._controller.start_countdown()
        self._take_photo_button.setEnabled(False)
        self._update_progress()
        self._countdown_worker = _CountdownWorker(self._controller)
        self._countdown_worker.countdown_failed.connect(
            self._recover_from_countdown_failure
        )
        self._countdown_worker.finished.connect(self._countdown_finished)
        self._countdown_worker.finished.connect(self._begin_capture)
        self._countdown_worker.start()

    def _show_countdown_tick(self, value: int) -> None:
        """Render a controller-owned countdown value delivered by Qt."""
        self._countdown_presentation.show_tick(value)

    def _present_booth_state(
        self, _previous_state: BoothState, state: BoothState
    ) -> None:
        """Present state-specific content without making workflow decisions."""
        if state is BoothState.COUNTDOWN:
            self._countdown_presentation.begin()
            return
        self._countdown_presentation.clear()
        if state is BoothState.PREPARING:
            self._clear_review_presentation()
            self._pages.setCurrentIndex(0)
        elif state is BoothState.PROCESSING:
            self._pages.setCurrentWidget(self._processing_presentation)
        elif state is BoothState.REVIEW:
            self._pages.setCurrentIndex(1)
        elif state is BoothState.ERROR:
            self._pages.setCurrentIndex(0)

    def _begin_capture(self) -> None:
        """Run the already-authorized capture outside the UI thread."""
        if self._is_stopping or self._controller.state is not BoothState.CAPTURING:
            return
        self._countdown_presentation.clear()
        self._preview.stop()
        self._capture_worker = _CaptureWorker(self._controller)
        self._capture_worker.capture_succeeded.connect(self._handle_capture_result)
        self._capture_worker.capture_failed.connect(self._recover_from_capture_failure)
        self._capture_worker.finished.connect(self._capture_worker_finished)
        self._capture_worker.start()

    def _recover_from_countdown_failure(self, message: str) -> None:
        """Leave recovery to the application's error presentation."""
        logger.warning("Countdown failed: %s", message)

    def _countdown_finished(self) -> None:
        """Release a finished countdown worker."""
        if self._countdown_worker is not None:
            self._countdown_worker.deleteLater()
            self._countdown_worker = None

    def _handle_capture_result(self, photo: Photo | None) -> None:
        """Resume preview after a non-final capture completes."""
        if photo is None:
            self._countdown_label.clear()
            self._take_photo_button.setEnabled(True)
            self._update_progress()
            self._preview.start()

    def _show_review(self, photo: Photo) -> None:
        """Present the final photo and transition the UI to review."""
        self._review_pixmap = photo_to_pixmap(photo)
        if self._review_pixmap.isNull():
            self._review_label.setText("Photo captured, but it could not be displayed.")
        else:
            self._review_label.setText("")
        self._review_status_label.setText("Your photo is ready")
        self._done_button.setEnabled(True)
        self._retake_button.setEnabled(True)
        self._pages.setCurrentIndex(1)
        self._update_review_pixmap()

    def _recover_from_capture_failure(self, message: str) -> None:
        """Leave recovery to the application's error presentation."""
        logger.warning("Capture failed: %s", message)

    def _capture_worker_finished(self) -> None:
        """Release the completed worker reference before another capture."""
        if self._capture_worker is not None:
            self._capture_worker.deleteLater()
            self._capture_worker = None

    def _finish_review(self) -> None:
        """Ask the application to persist and close the reviewed session."""
        self._done_button.setEnabled(False)
        self._retake_button.setEnabled(False)
        self._review_status_label.setText("Saving your photo…")
        self._completion_worker = _CompletionWorker(self._controller)
        self._completion_worker.completion_failed.connect(self._show_completion_error)
        self._completion_worker.finished.connect(self._completion_worker_finished)
        self._completion_worker.start()

    def _show_completion_error(self, _message: str) -> None:
        """Offer a retry without exposing storage implementation details."""
        self._review_status_label.setText("We couldn't save your photo.")
        self._done_button.setEnabled(True)
        self._retake_button.setEnabled(True)

    def _completion_worker_finished(self) -> None:
        """Release the completed session worker."""
        if self._completion_worker is not None:
            self._completion_worker.deleteLater()
            self._completion_worker = None

    def _retake(self) -> None:
        """Return from review to idle preview for another capture."""
        self._controller.retake()

    def _clear_review_presentation(self) -> None:
        """Discard completed-photo pixels and controls from the prior customer."""
        self._review_pixmap = None
        self._review_label.clear()
        self._review_status_label.setText("Your photo is ready")
        self._done_button.setEnabled(True)
        self._retake_button.setEnabled(True)

    def _update_progress(self) -> None:
        """Render progress from the controller-owned capture session."""
        session = self._controller.session
        if session is None:
            self._progress_label.clear()
            return
        self._progress_label.setText(
            f"Photo {session.photo_count + 1} of {session.target_photo_count}"
        )

    def _update_review_pixmap(self) -> None:
        """Fit the current reviewed image within its display area."""
        if self._review_pixmap is None or self._review_pixmap.isNull():
            return

        self._review_label.setPixmap(
            self._review_pixmap.scaled(
                self._review_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
