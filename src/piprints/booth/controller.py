"""Application-level coordination for the basic booth capture workflow."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from piprints.booth.state import BoothState
from piprints.camera import Camera

logger = logging.getLogger(__name__)


class BoothCaptureError(RuntimeError):
    """Raised when the booth cannot complete a requested photo capture."""


class BoothStateError(RuntimeError):
    """Raised when an operation is not valid in the current booth state."""


class BoothController:
    """Coordinate camera captures and state for the initial booth workflow."""

    def __init__(self, camera: Camera, capture_directory: Path) -> None:
        self._camera = camera
        self._capture_directory = capture_directory
        self._state = BoothState.IDLE
        self._last_capture: Path | None = None

    @property
    def state(self) -> BoothState:
        """Return the current booth workflow state."""
        return self._state

    @property
    def last_capture(self) -> Path | None:
        """Return the most recently captured image, if one is under review."""
        return self._last_capture

    def start_countdown(self) -> None:
        """Transition the booth from idle preview to countdown."""
        self._require_state(BoothState.IDLE)
        self._state = BoothState.COUNTDOWN
        logger.info("Booth countdown started")

    def capture(self) -> Path:
        """Capture a still image and transition to review.

        Call this from a worker thread because the underlying camera operation
        may take time to switch modes and write the image.
        """
        self._require_state(BoothState.COUNTDOWN)
        self._state = BoothState.CAPTURING
        destination = self._next_capture_path()

        try:
            captured_image = self._camera.capture(destination)
        except Exception as error:
            self._state = BoothState.IDLE
            logger.exception("Booth capture failed")
            raise BoothCaptureError("Unable to capture a photo.") from error

        self._last_capture = captured_image
        self._state = BoothState.REVIEW
        logger.info("Booth capture complete: %s", captured_image)
        return captured_image

    def retake(self) -> None:
        """Discard the review selection and return to idle preview."""
        self._require_state(BoothState.REVIEW)
        self._last_capture = None
        self._state = BoothState.IDLE
        logger.info("Booth returned to preview for a retake")

    def _next_capture_path(self) -> Path:
        """Return a unique runtime path for the next captured image."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        return self._capture_directory / f"capture-{timestamp}.jpg"

    def _require_state(self, expected_state: BoothState) -> None:
        """Ensure an operation is valid for the current workflow state."""
        if self._state is not expected_state:
            raise BoothStateError(
                f"Operation requires {expected_state.name}; current state is "
                f"{self._state.name}."
            )
