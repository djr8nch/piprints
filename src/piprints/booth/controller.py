"""Application-level coordination for the basic booth capture workflow."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from piprints.booth.countdown import Countdown
from piprints.booth.state import BoothState
from piprints.camera import Camera
from piprints.imaging import Photo, PhotoLoader, PhotoPipeline
from piprints.imaging.layouts import Layout
from piprints.session import CaptureSession

logger = logging.getLogger(__name__)


class BoothCaptureError(RuntimeError):
    """Raised when the booth cannot complete a requested photo capture."""


class BoothStateError(RuntimeError):
    """Raised when an operation is not valid in the current booth state."""


class BoothController:
    """Coordinate camera captures, session progress, and final composition."""

    def __init__(
        self,
        camera: Camera,
        capture_directory: Path,
        photo_loader: PhotoLoader,
        photo_pipeline: PhotoPipeline,
        layout: Layout,
        countdown_duration_seconds: int = 3,
    ) -> None:
        self._camera = camera
        self._capture_directory = capture_directory
        self._photo_loader = photo_loader
        self._photo_pipeline = photo_pipeline
        self._layout = layout
        self._state = BoothState.IDLE
        self._last_capture: Photo | None = None
        self._session: CaptureSession | None = None
        self._countdown = Countdown(countdown_duration_seconds)

    @property
    def state(self) -> BoothState:
        """Return the current booth workflow state."""
        return self._state

    @property
    def last_capture(self) -> Photo | None:
        """Return the completed layout currently under review, if any."""
        return self._last_capture

    @property
    def session(self) -> CaptureSession | None:
        """Return the active capture session, if one has been started."""
        return self._session

    def start_countdown(self) -> int:
        """Start countdown for the next session photo and return its display value."""
        self._require_state(BoothState.IDLE)
        if self._session is None:
            self._session = CaptureSession(self._layout.required_photos)
        self._state = BoothState.COUNTDOWN
        logger.info(
            "Booth countdown started for photo %d of %d",
            self._session.photo_count + 1,
            self._session.target_photo_count,
        )
        return self._countdown.start()

    def advance_countdown(self) -> int | None:
        """Advance countdown and return ``None`` when the capture should begin."""
        self._require_state(BoothState.COUNTDOWN)
        return self._countdown.advance()

    def capture(self) -> Photo | None:
        """Capture one still image and compose only when the session is complete.

        Call this from a worker thread because the underlying camera operation
        may take time to switch modes and write the image.

        Returns the final layout photo when the last required capture succeeds;
        otherwise returns ``None`` so the caller can resume preview for the
        next countdown.
        """
        self._require_state(BoothState.COUNTDOWN)
        self._state = BoothState.CAPTURING
        destination = self._next_capture_path()

        try:
            captured_image = self._camera.capture(destination)
            captured_photo = self._photo_loader.load(captured_image)
            processed_photo = self._photo_pipeline.process(captured_photo)
            session = self._require_session()
            session.add_photo(processed_photo)
        except Exception as error:
            self._state = BoothState.IDLE
            self._session = None
            logger.exception("Booth capture failed")
            raise BoothCaptureError("Unable to capture a photo.") from error

        if not session.is_complete:
            self._state = BoothState.IDLE
            logger.info(
                "Booth capture complete: %s (%d of %d)",
                captured_image,
                session.photo_count,
                session.target_photo_count,
            )
            return None

        try:
            final_photo = self._layout.compose(session.photos)
        except Exception as error:
            self._state = BoothState.IDLE
            self._session = None
            logger.exception("Booth layout composition failed")
            raise BoothCaptureError("Unable to compose the captured photos.") from error

        self._last_capture = final_photo
        self._state = BoothState.REVIEW
        logger.info("Booth session complete: %s", captured_image)
        return final_photo

    def retake(self) -> None:
        """Discard the review selection and return to idle preview."""
        self._require_state(BoothState.REVIEW)
        self._last_capture = None
        self._session = None
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

    def _require_session(self) -> CaptureSession:
        """Return the active session required while a capture is in progress."""
        if self._session is None:
            raise BoothStateError("Capture requires an active capture session.")
        return self._session
