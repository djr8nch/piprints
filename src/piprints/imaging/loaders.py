"""Adapters that turn external image sources into PiPrints photos."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, UnidentifiedImageError

from piprints.imaging.exceptions import InvalidPhotoError
from piprints.imaging.models import Photo


class PhotoLoader:
    """Load filesystem-backed camera captures into in-memory photos."""

    def load(self, path: Path) -> Photo:
        """Read ``path`` as an independent RGB photo.

        The source file is closed before the returned image leaves this
        boundary, so file lifecycle remains outside the Photo model.
        """
        try:
            with Image.open(path) as image:
                return Photo(image.convert("RGB").copy())
        except (OSError, UnidentifiedImageError) as error:
            raise InvalidPhotoError(f"Unable to read photo from {path}.") from error
