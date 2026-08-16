"""Deterministic, pixel-independent aspect-ratio framing decisions."""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd

from piprints.imaging.exceptions import InvalidAspectRatioError, InvalidCropError


@dataclass(frozen=True)
class AspectRatio:
    """A positive integer width-to-height aspect ratio."""

    width: int
    height: int

    def __post_init__(self) -> None:
        """Reject dimensions that cannot describe a target ratio."""
        if not _is_positive_integer(self.width) or not _is_positive_integer(
            self.height
        ):
            raise InvalidAspectRatioError(
                "Aspect-ratio dimensions must be positive integers."
            )
        divisor = gcd(self.width, self.height)
        object.__setattr__(self, "width", self.width // divisor)
        object.__setattr__(self, "height", self.height // divisor)


@dataclass(frozen=True)
class CropBox:
    """A half-open rectangular region using integer pixel coordinates."""

    left: int
    top: int
    right: int
    bottom: int

    def __post_init__(self) -> None:
        """Validate a crop shape independent of any source image bounds."""
        coordinates = (self.left, self.top, self.right, self.bottom)
        if not all(_is_integer_coordinate(coordinate) for coordinate in coordinates):
            raise InvalidCropError("Crop coordinates must be integers.")
        if self.left < 0 or self.top < 0:
            raise InvalidCropError("Crop coordinates cannot be negative.")
        if self.right <= self.left or self.bottom <= self.top:
            raise InvalidCropError("Crop bounds must have positive width and height.")

    @property
    def width(self) -> int:
        """Return the crop width in pixels."""
        return self.right - self.left

    @property
    def height(self) -> int:
        """Return the crop height in pixels."""
        return self.bottom - self.top

    def as_tuple(self) -> tuple[int, int, int, int]:
        """Return coordinates in Pillow's crop argument order."""
        return (self.left, self.top, self.right, self.bottom)


class CenterCropAspectRatioStrategy:
    """Calculate the largest centered crop that exactly fits a target ratio."""

    def crop_box(
        self, source_width: int, source_height: int, target_ratio: AspectRatio
    ) -> CropBox:
        """Return the centered target-ratio rectangle within source dimensions.

        Whole target-ratio units are used so the returned rectangle matches the
        requested ratio exactly. If centering leaves one extra pixel, it stays
        on the right or bottom edge for deterministic integer coordinates.
        """
        if not _is_positive_integer(source_width) or not _is_positive_integer(
            source_height
        ):
            raise InvalidCropError("Source dimensions must be positive integers.")

        multiplier = min(
            source_width // target_ratio.width,
            source_height // target_ratio.height,
        )
        if multiplier == 0:
            raise InvalidCropError(
                "Source dimensions are too small for one target-ratio unit."
            )

        crop_width = target_ratio.width * multiplier
        crop_height = target_ratio.height * multiplier
        left = (source_width - crop_width) // 2
        top = (source_height - crop_height) // 2
        return CropBox(left, top, left + crop_width, top + crop_height)


def _is_positive_integer(value: int) -> bool:
    """Return whether a value is an integer pixel dimension greater than zero."""
    return _is_integer_coordinate(value) and value > 0


def _is_integer_coordinate(value: int) -> bool:
    """Return whether a value is an integer that is not a boolean."""
    return isinstance(value, int) and not isinstance(value, bool)
