"""In-memory artifacts associated with one photo booth interaction."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID, uuid4

from piprints.imaging import Photo


class BoothSessionError(ValueError):
    """Raised when a booth session invariant would be violated."""


class BoothSession:
    """Collect the identity and image artifacts for one booth interaction.

    This model has no camera, layout, persistence, printing, or user-interface
    behavior. Workflow orchestration decides when photos are captured and when
    a composed output is assigned.
    """

    def __init__(
        self,
        target_photo_count: int = 1,
        session_id: UUID | None = None,
        layout_identifier: str | None = None,
        theme_identifier: str | None = None,
    ) -> None:
        if (
            isinstance(target_photo_count, bool)
            or not isinstance(target_photo_count, int)
            or target_photo_count <= 0
        ):
            raise BoothSessionError("Target photo count must be a positive integer.")
        if session_id is not None and not isinstance(session_id, UUID):
            raise BoothSessionError("Session ID must be a UUID.")
        if layout_identifier is not None and not layout_identifier:
            raise BoothSessionError("Layout identifier cannot be empty.")
        if theme_identifier is not None and not theme_identifier:
            raise BoothSessionError("Theme identifier cannot be empty.")
        self._id = session_id or uuid4()
        self._target_photo_count = target_photo_count
        self._layout_identifier = layout_identifier
        self._theme_identifier = theme_identifier
        self._captured_photos: list[Photo] = []
        self._final_photo: Photo | None = None

    @property
    def id(self) -> UUID:
        """Return this session's stable unique identifier."""
        return self._id

    @property
    def captured_photos(self) -> Sequence[Photo]:
        """Return an immutable snapshot of captured photos in capture order."""
        return tuple(self._captured_photos)

    @property
    def target_photo_count(self) -> int:
        """Return the layout-derived number of captures required by this session."""
        return self._target_photo_count

    @property
    def layout_identifier(self) -> str | None:
        """Return the application-selected layout for this session."""
        return self._layout_identifier

    @property
    def theme_identifier(self) -> str | None:
        """Return the application-selected theme for this session."""
        return self._theme_identifier

    @property
    def photo_count(self) -> int:
        """Return the number of photos captured during this session."""
        return len(self._captured_photos)

    @property
    def remaining_photos(self) -> int:
        """Return the number of captures still needed for the selected layout."""
        return self._target_photo_count - self.photo_count

    @property
    def is_complete(self) -> bool:
        """Return whether every required capture has been recorded."""
        return self.photo_count == self._target_photo_count

    @property
    def final_photo(self) -> Photo | None:
        """Return the composed session output when one has been assigned."""
        return self._final_photo

    def add_captured_photo(self, photo: Photo) -> None:
        """Record one captured photo before a final output is assigned."""
        if not isinstance(photo, Photo):
            raise BoothSessionError("Captured photos must be Photo instances.")
        if self._final_photo is not None:
            raise BoothSessionError(
                "Cannot add captured photos after assigning the final photo."
            )
        if self.is_complete:
            raise BoothSessionError(
                "Cannot add a photo to a complete booth session."
            )
        self._captured_photos.append(photo)

    def set_final_photo(self, photo: Photo) -> None:
        """Assign the one composed output for this session."""
        if not isinstance(photo, Photo):
            raise BoothSessionError("Final photo must be a Photo instance.")
        if not self.is_complete:
            raise BoothSessionError(
                "Cannot assign a final photo before all required photos are captured."
            )
        if self._final_photo is not None:
            raise BoothSessionError("A final photo has already been assigned.")
        self._final_photo = photo
