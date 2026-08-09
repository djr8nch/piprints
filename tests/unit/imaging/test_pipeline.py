"""Unit tests for ordered, per-photo pipeline composition."""

from __future__ import annotations

from PIL import Image

from piprints.imaging import Photo, PhotoPipeline


def make_photo(color: str = "black") -> Photo:
    """Create a small deterministic photo for imaging tests."""
    return Photo(Image.new("RGB", (2, 2), color))


class RecordingOperation:
    """Replace the photo and record the input for composition assertions."""

    def __init__(self, replacement: Photo) -> None:
        self.replacement = replacement
        self.inputs: list[Photo] = []

    def apply(self, photo: Photo) -> Photo:
        """Record the input and return the configured replacement."""
        self.inputs.append(photo)
        return self.replacement


def test_empty_pipeline_returns_the_original_photo() -> None:
    """An empty pipeline is an intentional no-op."""
    photo = make_photo()

    assert PhotoPipeline().process(photo) is photo


def test_pipeline_applies_operations_in_order() -> None:
    """Each operation receives the result returned by its predecessor."""
    original = make_photo("black")
    first_result = make_photo("red")
    final_result = make_photo("blue")
    first = RecordingOperation(first_result)
    second = RecordingOperation(final_result)

    result = PhotoPipeline([first, second]).process(original)

    assert first.inputs == [original]
    assert second.inputs == [first_result]
    assert result is final_result
