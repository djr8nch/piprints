"""Widgets for presenting live frames from a PiPrints camera."""

from __future__ import annotations

import logging
from queue import Empty, Full, Queue

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QImage, QPixmap, QResizeEvent
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from piprints.camera import Camera, CameraPreviewError, PreviewFrame

logger = logging.getLogger(__name__)

_FRAME_DISPLAY_INTERVAL_MS = 33


class _PreviewFrameWorker(QThread):
    """Read blocking camera frames away from the Qt UI thread."""

    preview_failed = Signal(str)

    def __init__(self, camera: Camera) -> None:
        super().__init__()
        self._camera = camera
        self._frames: Queue[PreviewFrame] = Queue(maxsize=1)

    def run(self) -> None:
        """Read frames until the preview is stopped or the camera fails."""
        while not self.isInterruptionRequested():
            try:
                frame = self._camera.capture_preview_frame()
            except CameraPreviewError as error:
                logger.exception("Camera preview frame retrieval failed")
                self.preview_failed.emit(str(error))
                return
            except Exception:
                logger.exception("Unexpected camera preview failure")
                self.preview_failed.emit("Camera preview stopped unexpectedly.")
                return

            self._store_latest_frame(frame)

    def take_latest_frame(self) -> PreviewFrame | None:
        """Return the latest available frame without waiting for a new one."""
        try:
            return self._frames.get_nowait()
        except Empty:
            return None

    def _store_latest_frame(self, frame: PreviewFrame) -> None:
        """Keep at most one frame so UI rendering cannot fall behind capture."""
        try:
            self._frames.put_nowait(frame)
        except Full:
            try:
                self._frames.get_nowait()
            except Empty:
                pass
            self._frames.put_nowait(frame)


class CameraPreviewWidget(QWidget):
    """Display frames supplied by a PiPrints-owned camera abstraction."""

    def __init__(self, camera: Camera) -> None:
        super().__init__()
        self._worker = _PreviewFrameWorker(camera)
        self._worker.preview_failed.connect(self._show_error)
        self._pixmap: QPixmap | None = None
        self._frame_timer = QTimer(self)
        self._frame_timer.setInterval(_FRAME_DISPLAY_INTERVAL_MS)
        self._frame_timer.timeout.connect(self._display_latest_frame)

        self._image_label = QLabel("Starting camera preview…")
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setStyleSheet("background-color: black; color: white;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._image_label)

    def start(self) -> None:
        """Begin receiving preview frames after the window becomes visible."""
        if not self._worker.isRunning():
            self._worker.start()
        self._frame_timer.start()

    def stop(self) -> None:
        """Stop frame retrieval before the camera is released."""
        self._frame_timer.stop()
        if not self._worker.isRunning():
            return

        self._worker.requestInterruption()
        if not self._worker.wait(2000):
            logger.warning("Camera preview worker did not stop within two seconds")

    def set_frame(self, frame: PreviewFrame) -> None:
        """Convert a PiPrints preview frame into a Qt pixmap for display."""
        image = QImage(
            frame.data,
            frame.width,
            frame.height,
            frame.bytes_per_line,
            QImage.Format.Format_RGB888,
        ).copy()
        self._pixmap = QPixmap.fromImage(image)
        self._update_pixmap()

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Scale the current preview while preserving its aspect ratio."""
        self._update_pixmap()
        super().resizeEvent(event)

    def _update_pixmap(self) -> None:
        """Fit the latest camera frame within the available widget space."""
        if self._pixmap is None:
            return

        self._image_label.setPixmap(
            self._pixmap.scaled(
                self._image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _display_latest_frame(self) -> None:
        """Present the newest worker frame without delaying camera acquisition."""
        frame = self._worker.take_latest_frame()
        if frame is not None:
            self.set_frame(frame)

    def _show_error(self, message: str) -> None:
        """Show a recoverable preview error in the preview area."""
        self._image_label.setText(f"Camera preview unavailable\n{message}")
