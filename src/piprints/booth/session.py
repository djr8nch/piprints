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

    def __init__(self, session_id: UUID | None = None) -> None:
        if session_id is not None and not isinstance(session_id, UUID):
            raise BoothSessionError("Session ID must be a UUID.")
        self._id = session_id or uuid4()
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
    def photo_count(self) -> int:
        """Return the number of photos captured during this session."""
        return len(self._captured_photos)

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
        self._captured_photos.append(photo)

    def set_final_photo(self, photo: Photo) -> None:
        """Assign the one composed output for this session."""
        if not isinstance(photo, Photo):
            raise BoothSessionError("Final photo must be a Photo instance.")
        if not self._captured_photos:
            raise BoothSessionError(
                "Cannot assign a final photo before capturing at least one photo."
            )
        if self._final_photo is not None:
            raise BoothSessionError("A final photo has already been assigned.")
        self._final_photo = photo
