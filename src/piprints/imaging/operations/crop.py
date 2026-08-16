"""Explicit pixel cropping for individual photos."""

from __future__ import annotations

from dataclasses import dataclass

from piprints.imaging.aspect_ratio import CropBox
from piprints.imaging.exceptions import InvalidCropError
from piprints.imaging.models import Photo


@dataclass(frozen=True)
class CropOperation:
    """Apply one explicit crop box without making framing decisions."""

    crop_box: CropBox

    def apply(self, photo: Photo) -> Photo:
        """Return a cropped photo after ensuring the box is within its bounds."""
        if (
            self.crop_box.right > photo.image.width
            or self.crop_box.bottom > photo.image.height
        ):
            raise InvalidCropError(
                "Crop bounds exceed the source photo dimensions "
                f"{photo.image.width}x{photo.image.height}."
            )
        return Photo(photo.image.crop(self.crop_box.as_tuple()))
