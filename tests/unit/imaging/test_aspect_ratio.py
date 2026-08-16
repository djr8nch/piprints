"""Unit tests for deterministic aspect-ratio framing."""

from __future__ import annotations

import pytest

from piprints.imaging import (
    AspectRatio,
    CenterCropAspectRatioStrategy,
    CropBox,
    InvalidAspectRatioError,
    InvalidCropError,
)


@pytest.fixture
def strategy() -> CenterCropAspectRatioStrategy:
    """Create the stateless center-crop framing strategy."""
    return CenterCropAspectRatioStrategy()


def test_source_already_matching_target_ratio_uses_full_image(
    strategy: CenterCropAspectRatioStrategy,
) -> None:
    """No pixels are discarded when the source already matches the ratio."""
    crop_box = strategy.crop_box(12, 18, AspectRatio(2, 3))

    assert crop_box == CropBox(0, 0, 12, 18)


def test_equivalent_ratios_are_normalized_before_framing(
    strategy: CenterCropAspectRatioStrategy,
) -> None:
    """Equivalent ratio inputs make the same full-image framing decision."""
    ratio = AspectRatio(2, 4)

    assert ratio == AspectRatio(1, 2)
    assert strategy.crop_box(3, 6, ratio) == CropBox(0, 0, 3, 6)


def test_landscape_source_crops_to_portrait_target(
    strategy: CenterCropAspectRatioStrategy,
) -> None:
    """A wide source loses equal horizontal regions around a centered crop."""
    crop_box = strategy.crop_box(16, 9, AspectRatio(2, 3))

    assert crop_box == CropBox(5, 0, 11, 9)


def test_portrait_source_crops_to_landscape_target(
    strategy: CenterCropAspectRatioStrategy,
) -> None:
    """A tall source loses equal vertical regions around a centered crop."""
    crop_box = strategy.crop_box(9, 16, AspectRatio(3, 2))

    assert crop_box == CropBox(0, 5, 9, 11)


def test_odd_remainder_stays_on_right_and_bottom(
    strategy: CenterCropAspectRatioStrategy,
) -> None:
    """Integer centering has stable behavior when discarded pixels are odd."""
    crop_box = strategy.crop_box(7, 8, AspectRatio(1, 1))

    assert crop_box == CropBox(0, 0, 7, 7)


@pytest.mark.parametrize("width,height", [(0, 1), (1, 0), (-1, 1), (1, -1)])
def test_aspect_ratio_rejects_invalid_dimensions(width: int, height: int) -> None:
    """A target ratio must have positive integer dimensions."""
    with pytest.raises(InvalidAspectRatioError, match="positive integers"):
        AspectRatio(width, height)


def test_crop_box_stays_in_source_bounds_and_matches_target_ratio(
    strategy: CenterCropAspectRatioStrategy,
) -> None:
    """The strategy returns an in-bounds exact integer-ratio crop."""
    crop_box = strategy.crop_box(17, 11, AspectRatio(4, 3))

    assert 0 <= crop_box.left < crop_box.right <= 17
    assert 0 <= crop_box.top < crop_box.bottom <= 11
    assert crop_box.width * 3 == crop_box.height * 4


def test_strategy_rejects_source_smaller_than_one_ratio_unit(
    strategy: CenterCropAspectRatioStrategy,
) -> None:
    """A crop cannot be calculated when no complete ratio unit fits."""
    with pytest.raises(InvalidCropError, match="too small"):
        strategy.crop_box(1, 1, AspectRatio(2, 3))
