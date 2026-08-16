"""A deterministic two-by-two four-photo composition layout."""

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
class FourPhotoLayout:
    """Arrange four photos in a square grid with a consistent white border."""

    canvas_width: int = 1200
    canvas_height: int = 1200
    margin: int = 40
    gutter: int = 20
    background: tuple[int, int, int] = (255, 255, 255)

    def __post_init__(self) -> None:
        """Validate geometry and ensure two equal cells fit each axis."""
        validate_layout_geometry(
            self.canvas_width, self.canvas_height, self.margin, self.gutter
        )
        available_width = self.canvas_width - 2 * self.margin - self.gutter
        available_height = self.canvas_height - 2 * self.margin - self.gutter
        if available_width <= 0 or available_height <= 0:
            raise ValueError("FourPhotoLayout margins leave no room for photo cells.")
        if available_width % 2 or available_height % 2:
            raise ValueError("FourPhotoLayout requires equal whole-pixel cells.")

    @property
    def required_photos(self) -> int:
        """Require exactly four processed photos."""
        return 4

    def compose(self, photos: Sequence[Photo]) -> Photo:
        """Compose four ordered photos from top-left to bottom-right."""
        if len(photos) != self.required_photos:
            raise InvalidPhotoCountError(
                f"FourPhotoLayout requires exactly four photos; received {len(photos)}."
            )
        cell_width = (self.canvas_width - 2 * self.margin - self.gutter) // 2
        cell_height = (self.canvas_height - 2 * self.margin - self.gutter) // 2
        canvas = new_canvas(self.canvas_width, self.canvas_height, self.background)
        for index, photo in enumerate(photos):
            column = index % 2
            row = index // 2
            x = self.margin + column * (cell_width + self.gutter)
            y = self.margin + row * (cell_height + self.gutter)
            cell_photo = fit_photo_to_cell(photo, cell_width, cell_height)
            canvas.paste(cell_photo.image, (x, y))
        return Photo(canvas)
