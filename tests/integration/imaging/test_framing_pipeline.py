"""Integration tests for the current single-photo framing pipeline."""

from __future__ import annotations

from PIL import Image

from piprints.imaging import (
    AspectRatio,
    CenterCropAspectRatioStrategy,
    Photo,
    PhotoPipeline,
)
from piprints.imaging.layouts import SinglePhotoLayout
from piprints.imaging.operations import CropOperation, ResizeOperation


class RecordingSinglePhotoLayout(SinglePhotoLayout):
    """Expose the processed input received by the real single-photo layout."""

    def __init__(self) -> None:
        self.received_photo: Photo | None = None

    def compose(self, photos: list[Photo]) -> Photo:
        """Record the processed photo before using normal layout behavior."""
        self.received_photo = photos[0]
        return super().compose(photos)


def test_center_crop_resize_pipeline_composes_a_final_photo() -> None:
    """The real framing, crop, resize, pipeline, and layout cooperate in memory."""
    photo = Photo(Image.new("RGB", (1600, 900), "blue"))
    ratio = AspectRatio(2, 3)
    crop_box = CenterCropAspectRatioStrategy().crop_box(
        photo.image.width, photo.image.height, ratio
    )
    pipeline = PhotoPipeline(
        [CropOperation(crop_box), ResizeOperation(width=400, height=600)]
    )
    layout = RecordingSinglePhotoLayout()

    processed_photo = pipeline.process(photo)
    final_photo = layout.compose([processed_photo])

    assert crop_box.width == 600
    assert crop_box.height == 900
    assert final_photo.image.size == (400, 600)
    assert (
        final_photo.image.width * ratio.height
        == final_photo.image.height * ratio.width
    )
    assert layout.received_photo is processed_photo
    assert final_photo is processed_photo
