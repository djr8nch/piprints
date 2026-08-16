"""Application-level coordination for the basic booth capture workflow."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from piprints.booth.countdown import Countdown
from piprints.booth.events import BoothEvent, BoothEventListener, BoothEventType
from piprints.booth.session import BoothSession
from piprints.booth.state import BoothState
from piprints.camera import Camera
from piprints.imaging import Photo, PhotoLoader, PhotoPipeline
from piprints.imaging.layouts import Layout

logger = logging.getLogger(__name__)


class BoothCaptureError(RuntimeError):
    """Raised when the booth cannot complete a requested photo capture."""


class BoothStateError(RuntimeError):
    """Raised when an operation is not valid in the current booth state."""


class BoothController:
    """Coordinate booth lifecycle transitions, captures, and composition."""

    _ALLOWED_TRANSITIONS: dict[BoothState, frozenset[BoothState]] = {
        BoothState.IDLE: frozenset({BoothState.PREPARING}),
        BoothState.PREPARING: frozenset({BoothState.COUNTDOWN, BoothState.IDLE}),
        BoothState.COUNTDOWN: frozenset({BoothState.CAPTURING, BoothState.ERROR}),
        BoothState.CAPTURING: frozenset(
            {BoothState.PREPARING, BoothState.PROCESSING, BoothState.ERROR}
        ),
        BoothState.PROCESSING: frozenset({BoothState.REVIEW, BoothState.ERROR}),
        BoothState.REVIEW: frozenset({BoothState.COMPLETE, BoothState.IDLE}),
        BoothState.COMPLETE: frozenset({BoothState.IDLE}),
        BoothState.ERROR: frozenset({BoothState.IDLE}),
    }

    def __init__(
        self,
        camera: Camera,
        capture_directory: Path,
        photo_loader: PhotoLoader,
        photo_pipeline: PhotoPipeline,
        layout: Layout,
        countdown_duration_seconds: int = 3,
        countdown: Countdown | None = None,
        listeners: Iterable[BoothEventListener] = (),
    ) -> None:
        self._camera = camera
        self._capture_directory = capture_directory
        self._photo_loader = photo_loader
        self._photo_pipeline = photo_pipeline
        self._layout = layout
        self._state = BoothState.IDLE
        self._session: BoothSession | None = None
        self._countdown = countdown or Countdown(countdown_duration_seconds)
        self._listeners: list[BoothEventListener] = []
        for listener in listeners:
            self.add_event_listener(listener)

    @property
    def state(self) -> BoothState:
        """Return the current booth workflow state."""
        return self._state

    @property
    def last_capture(self) -> Photo | None:
        """Return the completed layout currently under review, if any."""
        return self._session.final_photo if self._session is not None else None

    @property
    def session(self) -> BoothSession | None:
        """Return the active capture session, if one has been started."""
        return self._session

    def add_event_listener(self, listener: BoothEventListener) -> None:
        """Subscribe a listener to events from this controller instance."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_event_listener(self, listener: BoothEventListener) -> None:
        """Stop sending events to a listener that no longer needs them."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def begin_session(self) -> BoothSession:
        """Create the active session and enter its preparation phase."""
        self._require_state(BoothState.IDLE)
        if self._session is not None:
            raise BoothStateError("Cannot begin a session while one is active.")
        self._session = BoothSession(self._layout.required_photos)
        self._publish(BoothEventType.SESSION_STARTED)
        self._transition_to(BoothState.PREPARING)
        logger.info("Booth session started: %s", self._session.id)
        return self._session

    def complete_session(self) -> None:
        """Mark a reviewed session complete pending its final reset."""
        self._require_state(BoothState.REVIEW)
        self._transition_to(BoothState.COMPLETE)
        self._publish(BoothEventType.SESSION_COMPLETED)
        logger.info("Booth session completed: %s", self._require_session().id)

    def finish_session(self) -> None:
        """Clear a completed session and return to idle."""
        self._require_state(BoothState.COMPLETE)
        session = self._require_session()
        self._session = None
        self._transition_to(BoothState.IDLE)
        logger.info("Booth session finished: %s", session.id)

    def reset_session(self) -> None:
        """Recover from a failed session and return the booth to idle."""
        self._require_state(BoothState.ERROR)
        self._transition_to(BoothState.IDLE)
        logger.info("Booth reset after a failed session")

    def start_countdown(self) -> None:
        """Enter the countdown state for the next required session photo."""
        if self._state is BoothState.IDLE:
            self.begin_session()
        self._require_state(BoothState.PREPARING)
        session = self._require_session()
        self._transition_to(BoothState.COUNTDOWN)
        logger.info(
            "Booth countdown started for photo %d of %d",
            session.photo_count + 1,
            session.target_photo_count,
        )

    def run_countdown(self) -> None:
        """Execute countdown ticks, then make the booth ready to capture.

        Call this from a worker when the configured delay can block. The
        Countdown ticks are published as events so presentation layers can
        observe them without taking ownership of timing.
        """
        self._require_state(BoothState.COUNTDOWN)
        try:
            for tick in self._countdown.ticks():
                self._publish(BoothEventType.COUNTDOWN_TICK, countdown_value=tick)
            self._transition_to(BoothState.CAPTURING)
        except Exception as error:
            self._abort_session(error)
            raise

    def capture(self) -> Photo | None:
        """Capture one still image and compose only when the session is complete.

        Call this from a worker thread because the underlying camera operation
        may take time to switch modes and write the image.

        Returns the final layout photo when the last required capture succeeds;
        otherwise returns ``None`` so the caller can resume preview for the
        next countdown.
        """
        self._require_state(BoothState.CAPTURING)
        destination = self._next_capture_path()

        try:
            captured_image = self._camera.capture(destination)
            captured_photo = self._photo_loader.load(captured_image)
            processed_photo = self._photo_pipeline.process(captured_photo)
            session = self._require_session()
            session.add_captured_photo(processed_photo)
            self._publish(BoothEventType.PHOTO_CAPTURED, photo=processed_photo)
        except Exception as error:
            self._abort_session(error)
            logger.exception("Booth capture failed")
            raise BoothCaptureError("Unable to capture a photo.") from error

        if not session.is_complete:
            self._transition_to(BoothState.PREPARING)
            logger.info(
                "Booth capture complete: %s (%d of %d)",
                captured_image,
                session.photo_count,
                session.target_photo_count,
            )
            return None

        try:
            self._transition_to(BoothState.PROCESSING)
            final_photo = self._layout.compose(session.captured_photos)
            session.set_final_photo(final_photo)
        except Exception as error:
            self._abort_session(error)
            logger.exception("Booth layout composition failed")
            raise BoothCaptureError("Unable to compose the captured photos.") from error

        self._transition_to(BoothState.REVIEW)
        self._publish(BoothEventType.REVIEW_READY, photo=final_photo)
        logger.info("Booth session complete: %s", captured_image)
        return final_photo

    def retake(self) -> None:
        """Discard the review selection and return to idle preview."""
        self._require_state(BoothState.REVIEW)
        self._session = None
        self._transition_to(BoothState.IDLE)
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

    def _transition_to(self, next_state: BoothState) -> None:
        """Move to an explicitly allowed lifecycle state."""
        if next_state not in self._ALLOWED_TRANSITIONS[self._state]:
            raise BoothStateError(
                f"Cannot transition from {self._state.name} to {next_state.name}."
            )
        previous_state = self._state
        self._state = next_state
        self._publish(
            BoothEventType.STATE_CHANGED,
            previous_state=previous_state,
        )

    def _abort_session(self, error: Exception) -> None:
        """Clear failed artifacts while leaving recovery at the error boundary."""
        self._transition_to(BoothState.ERROR)
        self._publish(BoothEventType.ERROR, message=str(error))
        self._session = None

    def _publish(
        self,
        event_type: BoothEventType,
        *,
        previous_state: BoothState | None = None,
        countdown_value: int | None = None,
        photo: Photo | None = None,
        message: str | None = None,
    ) -> None:
        """Notify listeners while isolating failures from booth workflow logic."""
        event = BoothEvent(
            event_type=event_type,
            state=self._state,
            session_id=self._session.id if self._session is not None else None,
            previous_state=previous_state,
            countdown_value=countdown_value,
            photo=photo,
            message=message,
        )
        for listener in tuple(self._listeners):
            try:
                listener.on_booth_event(event)
            except Exception:
                logger.exception(
                    "Booth event listener failed while handling %s", event.event_type
                )

    def _require_session(self) -> BoothSession:
        """Return the active session required while a capture is in progress."""
        if self._session is None:
            raise BoothStateError("Capture requires an active capture session.")
        return self._session
