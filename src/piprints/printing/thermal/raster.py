"""Deterministic conversion of PiPrints photos into thermal raster bytes."""

from __future__ import annotations

from dataclasses import dataclass

from piprints.imaging import Photo


@dataclass(frozen=True)
class ThermalRaster:
    """Monochrome row-major bytes produced for a thermal printer protocol.

    Each row occupies ``bytes_per_row`` bytes. In every byte, the leftmost
    pixel is the most-significant bit. A set bit represents a black dot; bits
    past ``width`` in the final byte of a row are white padding.
    """

    data: bytes
    width: int
    height: int
    bytes_per_row: int


class ThermalRasterEncoder:
    """Encode prepared RGB photos into deterministic monochrome raster data."""

    def __init__(self, *, max_width: int | None = None, threshold: int = 128) -> None:
        if (
            max_width is not None
            and (
                isinstance(max_width, bool)
                or not isinstance(max_width, int)
                or max_width <= 0
            )
        ):
            raise ValueError("Maximum thermal raster width must be a positive integer.")
        if (
            isinstance(threshold, bool)
            or not isinstance(threshold, int)
            or not 0 <= threshold <= 255
        ):
            raise ValueError(
                "Thermal raster threshold must be an integer from 0 to 255."
            )
        self._max_width = max_width
        self._threshold = threshold

    def encode(self, photo: Photo) -> ThermalRaster:
        """Convert a prepared photo to monochrome, byte-aligned raster data.

        Photos wider than an explicitly configured ``max_width`` are rejected
        rather than implicitly resized. A future printer-specific preparation
        step can make resizing an intentional, testable decision.
        """
        image = photo.image
        if self._max_width is not None and image.width > self._max_width:
            raise ValueError(
                f"Photo width {image.width} exceeds thermal raster maximum "
                f"of {self._max_width} dots."
            )

        monochrome = image.convert("L")
        bytes_per_row = (monochrome.width + 7) // 8
        raster_data = bytearray(bytes_per_row * monochrome.height)
        pixels = monochrome.load()

        for y in range(monochrome.height):
            row_offset = y * bytes_per_row
            for x in range(monochrome.width):
                if pixels[x, y] < self._threshold:
                    raster_data[row_offset + x // 8] |= 1 << (7 - x % 8)

        return ThermalRaster(
            data=bytes(raster_data),
            width=monochrome.width,
            height=monochrome.height,
            bytes_per_row=bytes_per_row,
        )
