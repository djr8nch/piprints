"""Per-photo resizing operation."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from piprints.imaging.models import Photo


@dataclass(frozen=True)
class ResizeOperation:
    """Resize a photo to exact positive pixel dimensions using Lanczos sampling."""

    width: int
    height: int

    def __post_init__(self) -> None:
        """Validate dimensions before an operation is used in a pipeline."""
        if (
            isinstance(self.width, bool)
            or isinstance(self.height, bool)
            or not isinstance(self.width, int)
            or not isinstance(self.height, int)
            or self.width <= 0
            or self.height <= 0
        ):
            raise ValueError("Resize dimensions must be positive integers.")

    def apply(self, photo: Photo) -> Photo:
        """Return a resized copy of ``photo`` without mutating its image."""
        resized_image = photo.image.resize(
            (self.width, self.height), Image.Resampling.LANCZOS
        )
        return Photo(resized_image)
