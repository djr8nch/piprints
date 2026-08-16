"""Domain model for the photos captured during one booth session."""

from __future__ import annotations

from collections.abc import Sequence

from piprints.imaging import Photo


class CaptureSessionError(ValueError):
    """Raised when a capture session invariant would be violated."""


class CaptureSession:
    """Collect a fixed number of processed photos for one booth session.

    The session deliberately has no knowledge of cameras, timers, layouts, or
    persistence. It is the domain source of truth for capture progress.
    """

    def __init__(self, target_photo_count: int) -> None:
        if (
            isinstance(target_photo_count, bool)
            or not isinstance(target_photo_count, int)
            or target_photo_count <= 0
        ):
            raise CaptureSessionError("Target photo count must be a positive integer.")
        self._target_photo_count = target_photo_count
        self._photos: list[Photo] = []

    @property
    def target_photo_count(self) -> int:
        """Return the fixed number of photos this session requires."""
        return self._target_photo_count

    @property
    def photos(self) -> Sequence[Photo]:
        """Return an immutable snapshot of the captured photos in order."""
        return tuple(self._photos)

    @property
    def photo_count(self) -> int:
        """Return the number of photos captured so far."""
        return len(self._photos)

    @property
    def remaining_photos(self) -> int:
        """Return the number of captures still required."""
        return self._target_photo_count - self.photo_count

    @property
    def is_complete(self) -> bool:
        """Return whether the session has every required photo."""
        return self.photo_count == self._target_photo_count

    def add_photo(self, photo: Photo) -> None:
        """Add one processed photo while preserving the configured maximum."""
        if self.is_complete:
            raise CaptureSessionError(
                "Cannot add a photo to a complete capture session."
            )
        self._photos.append(photo)
