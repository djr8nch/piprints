"""Application-level coordination for the basic booth capture workflow."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from piprints.booth.countdown import Countdown
from piprints.booth.events import (
    BoothErrorCategory,
    BoothEvent,
    BoothEventListener,
    BoothEventType,
)
from piprints.booth.layout_selection import LayoutCatalog, LayoutOption
from piprints.booth.session import BoothSession
from piprints.booth.state import BoothState
from piprints.camera import (
    Camera,
    CameraCaptureError,
    CameraNotStartedError,
    CameraPreviewError,
    CameraStartupError,
)
from piprints.imaging import Photo, PhotoLoader, PhotoPipeline
from piprints.imaging.layouts import Layout
from piprints.printing import Printer, PrintError, PrintResult
from piprints.storage import PhotoStorage, StorageError
from piprints.themes import ThemeCatalog, ThemeOption

logger = logging.getLogger(__name__)


class BoothCaptureError(RuntimeError):
    """Raised when the booth cannot complete a requested photo capture."""


class BoothStateError(RuntimeError):
    """Raised when an operation is not valid in the current booth state."""


class BoothStorageError(RuntimeError):
    """Raised when the completed session output cannot be persisted."""


class BoothPrintError(RuntimeError):
    """Raised when a saved completed session output cannot be printed."""


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
        photo_storage: PhotoStorage,
        printer: Printer | None = None,
        countdown_duration_seconds: int = 3,
        countdown: Countdown | None = None,
        listeners: Iterable[BoothEventListener] = (),
        layout_catalog: LayoutCatalog | None = None,
        theme_catalog: ThemeCatalog | None = None,
    ) -> None:
        self._camera = camera
        self._capture_directory = capture_directory
        self._photo_loader = photo_loader
        self._photo_pipeline = photo_pipeline
        self._layout_catalog = layout_catalog or self._catalog_for_layout(layout)
        self._theme_catalog = theme_catalog or ThemeCatalog(
            (ThemeOption("default", "PiPrints"),)
        )
        self._layout = layout
        self._photo_storage = photo_storage
        self._printer = printer
        self._state = BoothState.IDLE
        self._session: BoothSession | None = None
        self._saved_output_path: Path | None = None
        self._print_completed = False
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

    @property
    def available_layouts(self) -> tuple[LayoutOption, ...]:
        """Return application-level descriptors for layouts users may select."""
        return self._layout_catalog.options

    @property
    def available_themes(self) -> tuple[ThemeOption, ...]:
        """Return application-level descriptors for usable theme choices."""
        return self._theme_catalog.options

    @property
    def printer_available(self) -> bool:
        """Return whether this booth has an application-configured printer."""
        return self._printer is not None

    @property
    def output_saved(self) -> bool:
        """Return whether the current review output has been stored successfully."""
        return self._saved_output_path is not None

    def add_event_listener(self, listener: BoothEventListener) -> None:
        """Subscribe a listener to events from this controller instance."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_event_listener(self, listener: BoothEventListener) -> None:
        """Stop sending events to a listener that no longer needs them."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def begin_session(
        self,
        layout_identifier: str | None = None,
        theme_identifier: str | None = None,
    ) -> BoothSession:
        """Create the active session and enter its preparation phase."""
        self._require_state(BoothState.IDLE)
        if self._session is not None:
            raise BoothStateError("Cannot begin a session while one is active.")
        selected_identifier = (
            layout_identifier or self._layout_catalog.default_identifier
        )
        selected_theme_identifier = (
            theme_identifier or self._theme_catalog.default_identifier
        )
        if not self._theme_catalog.contains(selected_theme_identifier):
            raise BoothStateError(f"Unsupported theme: {selected_theme_identifier!r}.")
        try:
            self._layout = self._layout_catalog.create(selected_identifier)
        except ValueError as error:
            raise BoothStateError(str(error)) from error
        self._session = BoothSession(
            self._layout.required_photos,
            layout_identifier=selected_identifier,
            theme_identifier=selected_theme_identifier,
        )
        self._saved_output_path = None
        self._print_completed = False
        self._publish(BoothEventType.SESSION_STARTED)
        self._transition_to(BoothState.PREPARING)
        logger.info("Booth session started: %s", self._session.id)
        return self._session

    def complete_session(self) -> None:
        """Persist the reviewed output, then mark the session complete.

        A persistence failure leaves the session in review so the caller can
        report the failure and retry without recapturing the photos. Printing
        is an explicit review action through :meth:`print_reviewed_output`.
        """
        self._require_state(BoothState.REVIEW)
        session = self._require_session()
        final_photo = session.final_photo
        if final_photo is None:
            raise BoothStateError("A reviewed session requires a final photo.")
        saved_path = self._save_output(session, final_photo)
        self._transition_to(BoothState.COMPLETE)
        self._publish(BoothEventType.SESSION_COMPLETED)
        logger.info("Booth session completed: %s saved to %s", session.id, saved_path)

    def print_reviewed_output(self) -> PrintResult:
        """Save once and submit the final reviewed layout to the printer.

        A successful request is limited to one print per review session to
        protect against repeated touch input. Failures retain both the review
        state and saved digital output so the user can retry or finish.
        """
        self._require_state(BoothState.REVIEW)
        if self._printer is None:
            raise BoothPrintError("No printer is configured for this booth.")
        if self._print_completed:
            raise BoothStateError("The reviewed photo has already been printed.")
        session = self._require_session()
        final_photo = session.final_photo
        if final_photo is None:
            raise BoothStateError("A reviewed session requires a final photo.")
        self._save_output(session, final_photo)
        print_result = self._print_output(session, final_photo)
        self._print_completed = True
        return print_result

    def _save_output(self, session: BoothSession, photo: Photo) -> Path:
        """Persist the final photo once and return its saved location."""
        if self._saved_output_path is not None:
            return self._saved_output_path
        try:
            saved_path = self._photo_storage.save(photo, session_id=session.id)
        except StorageError as error:
            logger.exception("Booth session output could not be saved: %s", session.id)
            self._publish(BoothEventType.OUTPUT_SAVE_FAILED, message=str(error))
            raise BoothStorageError("Unable to save the completed photo.") from error
        self._saved_output_path = saved_path
        self._publish(BoothEventType.OUTPUT_SAVED, output_path=saved_path)
        logger.info("Booth session output saved: %s", saved_path)
        return saved_path

    def _print_output(self, session: BoothSession, photo: Photo) -> PrintResult:
        """Submit the final photo to the configured printer."""
        try:
            print_result = self._printer.print_photo(photo)
        except PrintError as error:
            logger.exception(
                "Booth session output could not be printed: %s", session.id
            )
            self._publish(BoothEventType.PRINT_FAILED, message=str(error))
            raise BoothPrintError("Unable to print the completed photo.") from error
        self._publish(BoothEventType.PRINT_COMPLETED, print_result=print_result)
        logger.info("Booth session output printed: %s", session.id)
        return print_result

    def finish_session(self) -> None:
        """Clear a completed session and return to idle."""
        self._require_state(BoothState.COMPLETE)
        session = self._require_session()
        self._session = None
        self._saved_output_path = None
        self._print_completed = False
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
            self._abort_session(error, BoothErrorCategory.PHOTO_CAPTURE_FAILED)
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
        except Exception as error:
            self._abort_session(error, self._camera_error_category(error))
            logger.exception("Booth camera capture failed")
            raise BoothCaptureError("Unable to capture a photo.") from error

        try:
            captured_photo = self._photo_loader.load(captured_image)
            processed_photo = self._photo_pipeline.process(captured_photo)
            session = self._require_session()
            session.add_captured_photo(processed_photo)
            self._publish(BoothEventType.PHOTO_CAPTURED, photo=processed_photo)
        except Exception as error:
            self._abort_session(error, BoothErrorCategory.PHOTO_PROCESSING_FAILED)
            logger.exception("Booth photo processing failed")
            raise BoothCaptureError("Unable to prepare a photo.") from error

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
            self._abort_session(error, BoothErrorCategory.PHOTO_PROCESSING_FAILED)
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
        self._saved_output_path = None
        self._print_completed = False
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

    def _abort_session(self, error: Exception, category: BoothErrorCategory) -> None:
        """Clear failed artifacts while leaving recovery at the error boundary."""
        self._transition_to(BoothState.ERROR)
        self._publish(
            BoothEventType.ERROR,
            error_category=category,
            message=str(error),
        )
        self._session = None

    def _publish(
        self,
        event_type: BoothEventType,
        *,
        previous_state: BoothState | None = None,
        countdown_value: int | None = None,
        photo: Photo | None = None,
        output_path: Path | None = None,
        print_result: PrintResult | None = None,
        error_category: BoothErrorCategory | None = None,
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
            output_path=output_path,
            print_result=print_result,
            error_category=error_category,
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

    @staticmethod
    def _camera_error_category(error: Exception) -> BoothErrorCategory:
        """Classify PiPrints camera errors without exposing adapter details to UI."""
        if isinstance(
            error,
            (CameraNotStartedError, CameraPreviewError, CameraStartupError),
        ):
            return BoothErrorCategory.CAMERA_UNAVAILABLE
        if isinstance(error, CameraCaptureError):
            return BoothErrorCategory.PHOTO_CAPTURE_FAILED
        return BoothErrorCategory.PHOTO_CAPTURE_FAILED

    @staticmethod
    def _catalog_for_layout(layout: Layout) -> LayoutCatalog:
        """Adapt legacy single-layout construction to the selection boundary."""
        option = LayoutOption(
            identifier="default",
            name="Photo Layout",
            description=f"{layout.required_photos} photo session",
            required_photos=layout.required_photos,
            preview_columns=1,
            preview_rows=1,
        )
        return LayoutCatalog((option,), {option.identifier: lambda: layout})
