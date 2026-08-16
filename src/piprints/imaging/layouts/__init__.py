"""Strategies that combine processed photos into final compositions."""

from piprints.imaging.layouts.base import Layout
from piprints.imaging.layouts.classic_photo_strip import ClassicPhotoStripLayout
from piprints.imaging.layouts.four_photo import FourPhotoLayout
from piprints.imaging.layouts.single_photo import SinglePhotoLayout

__all__ = [
    "ClassicPhotoStripLayout",
    "FourPhotoLayout",
    "Layout",
    "SinglePhotoLayout",
]
