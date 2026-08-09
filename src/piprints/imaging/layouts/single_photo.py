"""The initial single-photo layout strategy."""

from __future__ import annotations

from collections.abc import Sequence

from piprints.imaging.exceptions import InvalidPhotoCountError
from piprints.imaging.models import Photo


class SinglePhotoLayout:
    """Return the sole processed photo as the final composition."""

    @property
    def required_photos(self) -> int:
        """Require exactly one photo."""
        return 1

    def compose(self, photos: Sequence[Photo]) -> Photo:
        """Return the sole photo or reject an invalid input count."""
        if len(photos) != self.required_photos:
            raise InvalidPhotoCountError(
                "SinglePhotoLayout requires exactly one photo; "
                f"received {len(photos)}."
            )
        return photos[0]
