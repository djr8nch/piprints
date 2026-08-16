"""Shared cell-fitting helpers for concrete Pillow layout strategies."""

from __future__ import annotations

from PIL import Image

from piprints.imaging import AspectRatio, CenterCropAspectRatioStrategy, Photo
from piprints.imaging.operations import CropOperation, ResizeOperation


def fit_photo_to_cell(photo: Photo, width: int, height: int) -> Photo:
    """Center-crop and resize one photo so it fills an exact layout cell."""
    ratio = AspectRatio(width, height)
    crop_box = CenterCropAspectRatioStrategy().crop_box(
        photo.image.width, photo.image.height, ratio
    )
    return ResizeOperation(width, height).apply(CropOperation(crop_box).apply(photo))


def new_canvas(
    width: int, height: int, background: tuple[int, int, int]
) -> Image.Image:
    """Create a validated RGB canvas for a layout."""
    return Image.new("RGB", (width, height), background)


def validate_layout_geometry(
    width: int, height: int, margin: int, gutter: int
) -> None:
    """Reject dimensions that cannot describe a concrete layout canvas."""
    dimensions = (width, height, margin, gutter)
    if any(
        isinstance(value, bool) or not isinstance(value, int) for value in dimensions
    ):
        raise ValueError("Layout geometry values must be integers.")
    if width <= 0 or height <= 0 or margin < 0 or gutter < 0:
        raise ValueError(
            "Canvas dimensions must be positive; margins and gutters nonnegative."
        )
