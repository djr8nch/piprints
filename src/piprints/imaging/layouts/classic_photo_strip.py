"""A deterministic four-photo vertical strip composition layout."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from piprints.imaging.exceptions import InvalidPhotoCountError
from piprints.imaging.layouts._cells import (
    fit_photo_to_cell,
    new_canvas,
    validate_layout_geometry,
)
from piprints.imaging.models import Photo


@dataclass(frozen=True)
class ClassicPhotoStripLayout:
    """Stack four photos vertically in a classic tall photo-strip format."""

    canvas_width: int = 600
    canvas_height: int = 2800
    margin: int = 30
    gutter: int = 20
    background: tuple[int, int, int] = (255, 255, 255)

    def __post_init__(self) -> None:
        """Validate geometry and ensure four equal whole-pixel cells fit."""
        validate_layout_geometry(
            self.canvas_width, self.canvas_height, self.margin, self.gutter
        )
        available_width = self.canvas_width - 2 * self.margin
        available_height = self.canvas_height - 2 * self.margin - 3 * self.gutter
        if available_width <= 0 or available_height <= 0:
            raise ValueError("Photo-strip margins leave no room for photo cells.")
        if available_height % self.required_photos:
            raise ValueError("Photo-strip layout requires equal whole-pixel cells.")

    @property
    def required_photos(self) -> int:
        """Require exactly four processed photos."""
        return 4

    def compose(self, photos: Sequence[Photo]) -> Photo:
        """Compose four ordered photos from top to bottom."""
        if len(photos) != self.required_photos:
            raise InvalidPhotoCountError(
                "ClassicPhotoStripLayout requires exactly four photos; "
                f"received {len(photos)}."
            )
        cell_width = self.canvas_width - 2 * self.margin
        cell_height = (
            self.canvas_height - 2 * self.margin - 3 * self.gutter
        ) // self.required_photos
        canvas = new_canvas(self.canvas_width, self.canvas_height, self.background)
        for index, photo in enumerate(photos):
            y = self.margin + index * (cell_height + self.gutter)
            cell_photo = fit_photo_to_cell(photo, cell_width, cell_height)
            canvas.paste(cell_photo.image, (self.margin, y))
        return Photo(canvas)
