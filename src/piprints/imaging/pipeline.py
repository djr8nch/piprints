"""Composable per-photo image-processing pipeline."""

from __future__ import annotations

from collections.abc import Iterable

from piprints.imaging.models import Photo
from piprints.imaging.operations.base import PhotoOperation


class PhotoPipeline:
    """Apply an ordered sequence of operations to one photo."""

    def __init__(self, operations: Iterable[PhotoOperation] = ()) -> None:
        self._operations = tuple(operations)

    def process(self, photo: Photo) -> Photo:
        """Return ``photo`` after applying each configured operation in order."""
        result = photo
        for operation in self._operations:
            result = operation.apply(result)
        return result
