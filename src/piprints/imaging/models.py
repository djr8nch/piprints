"""Image-domain models owned by PiPrints."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from piprints.imaging.exceptions import InvalidPhotoError


@dataclass(frozen=True)
class Photo:
    """An in-memory RGB photo ready for PiPrints imaging operations.

    The model deliberately does not retain a capture path. File lifecycle and
    persistence remain outside the imaging subsystem.
    """

    image: Image.Image

    def __post_init__(self) -> None:
        """Reject images that cannot be safely passed between operations."""
        if self.image.mode != "RGB":
            raise InvalidPhotoError("Photo images must use RGB color mode.")
        if self.image.width <= 0 or self.image.height <= 0:
            raise InvalidPhotoError("Photo images must have positive dimensions.")
