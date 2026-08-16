"""Byte-level tests for thermal raster encoding."""

import pytest
from PIL import Image

from piprints.imaging import Photo
from piprints.printing.thermal import ThermalRasterEncoder


def photo_from_pixels(
    width: int, height: int, pixels: list[tuple[int, int, int]]
) -> Photo:
    """Create one RGB photo from row-major test pixels."""
    image = Image.new("RGB", (width, height))
    image.putdata(pixels)
    return Photo(image)


def test_encoder_packs_white_pixels_as_clear_bits() -> None:
    """Eight white pixels become one all-clear raster byte."""
    raster = ThermalRasterEncoder().encode(
        Photo(Image.new("RGB", (8, 1), "white"))
    )

    assert raster.data == b"\x00"
    assert raster.bytes_per_row == 1


def test_encoder_packs_black_pixels_as_set_bits() -> None:
    """Eight black pixels become one all-set raster byte."""
    raster = ThermalRasterEncoder().encode(
        Photo(Image.new("RGB", (8, 1), "black"))
    )

    assert raster.data == b"\xff"


def test_encoder_packs_leftmost_pixel_into_the_most_significant_bit() -> None:
    """Alternating black and white pixels produce an easily auditable byte."""
    black = (0, 0, 0)
    white = (255, 255, 255)

    raster = ThermalRasterEncoder().encode(
        photo_from_pixels(8, 1, [black, white] * 4)
    )

    assert raster.data == b"\xaa"


def test_encoder_pads_the_final_partial_byte_with_white_bits() -> None:
    """A non-byte-aligned row never introduces black padding dots."""
    black = (0, 0, 0)
    white = (255, 255, 255)

    raster = ThermalRasterEncoder().encode(
        photo_from_pixels(5, 1, [black, white, black, white, black])
    )

    assert raster.data == b"\xa8"
    assert raster.width == 5
    assert raster.height == 1
    assert raster.bytes_per_row == 1


def test_encoder_preserves_row_order() -> None:
    """Each source row is emitted before the next row's packed bytes."""
    black = (0, 0, 0)
    white = (255, 255, 255)

    raster = ThermalRasterEncoder().encode(
        photo_from_pixels(8, 2, [black] + [white] * 14 + [black])
    )

    assert raster.data == b"\x80\x01"


def test_encoder_uses_a_deterministic_grayscale_threshold() -> None:
    """Values below the threshold are black; equal values remain white."""
    raster = ThermalRasterEncoder().encode(
        photo_from_pixels(2, 1, [(127, 127, 127), (128, 128, 128)])
    )

    assert raster.data == b"\x80"


def test_encoder_can_dither_grayscale_with_floyd_steinberg_diffusion() -> None:
    """Dithering represents tones as a deterministic pattern of thermal dots."""
    pixels = [
        (value, value, value)
        for value in (
            32,
            64,
            96,
            128,
            160,
            192,
            224,
            240,
            240,
            224,
            192,
            160,
            128,
            96,
            64,
            32,
        )
    ]

    raster = ThermalRasterEncoder(dither=True).encode(photo_from_pixels(8, 2, pixels))

    assert raster.data == b"\xd0\x17"


def test_encoder_applies_contrast_before_dithering() -> None:
    """A contrast adjustment intentionally affects the thermal dot pattern."""
    photo = photo_from_pixels(2, 1, [(120, 120, 120), (126, 126, 126)])

    raster = ThermalRasterEncoder(contrast=2.0).encode(photo)

    assert raster.data == b"\x80"


def test_encoder_applies_brightness_before_thresholding() -> None:
    """Brightness lifting can preserve detail that would otherwise print black."""
    photo = photo_from_pixels(1, 1, [(100, 100, 100)])

    raster = ThermalRasterEncoder(brightness=1.5).encode(photo)

    assert raster.data == b"\x00"


def test_encoder_lifts_midtones_with_gamma_before_thresholding() -> None:
    """A sub-one gamma value brightens facial-range midtones without new hardware."""
    photo = photo_from_pixels(1, 1, [(128, 128, 128)])

    raster = ThermalRasterEncoder(gamma=0.5).encode(photo)

    assert raster.data == b"\x00"


def test_encoder_reports_byte_aligned_dimensions_for_larger_images() -> None:
    """Output shape is derivable without any printer transport behavior."""
    raster = ThermalRasterEncoder().encode(Photo(Image.new("RGB", (9, 3), "black")))

    assert raster.width == 9
    assert raster.height == 3
    assert raster.bytes_per_row == 2
    assert len(raster.data) == 6
    assert raster.data == b"\xff\x80" * 3


def test_encoder_rejects_images_wider_than_its_configured_limit() -> None:
    """Width preparation is explicit rather than an implicit resize."""
    encoder = ThermalRasterEncoder(max_width=8)

    with pytest.raises(ValueError, match="exceeds thermal raster maximum"):
        encoder.encode(Photo(Image.new("RGB", (9, 1), "black")))


def test_encoder_can_explicitly_fit_an_oversized_photo_to_its_maximum_width() -> None:
    """Printer composition can request a proportional fit for a known print head."""
    raster = ThermalRasterEncoder(max_width=8, fit_to_max_width=True).encode(
        Photo(Image.new("RGB", (16, 4), "black"))
    )

    assert raster.width == 8
    assert raster.height == 2
    assert raster.data == b"\xff\xff"


@pytest.mark.parametrize("max_width", [0, -1, 1.5, True])
def test_encoder_rejects_invalid_maximum_width(max_width: object) -> None:
    """Configured dot limits must be positive integer values."""
    with pytest.raises(ValueError, match="positive integer"):
        ThermalRasterEncoder(max_width=max_width)  # type: ignore[arg-type]


@pytest.mark.parametrize("threshold", [-1, 256, 1.5, True])
def test_encoder_rejects_invalid_threshold(threshold: object) -> None:
    """Configured thresholds must fit a grayscale byte."""
    with pytest.raises(ValueError, match="integer from 0 to 255"):
        ThermalRasterEncoder(threshold=threshold)  # type: ignore[arg-type]


@pytest.mark.parametrize("fit_to_max_width", [0, "yes", None])
def test_encoder_rejects_non_boolean_fit_to_width_setting(
    fit_to_max_width: object,
) -> None:
    """Fitting behavior must be an explicit configuration choice."""
    with pytest.raises(ValueError, match="fit-to-width setting"):
        ThermalRasterEncoder(
            fit_to_max_width=fit_to_max_width  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("dither", [0, "yes", None])
def test_encoder_rejects_non_boolean_dithering_setting(dither: object) -> None:
    """Dithering must be an explicit encoder configuration choice."""
    with pytest.raises(ValueError, match="dithering setting"):
        ThermalRasterEncoder(dither=dither)  # type: ignore[arg-type]


@pytest.mark.parametrize("contrast", [0, -1, 1.5j, "more", True])
def test_encoder_rejects_invalid_contrast(contrast: object) -> None:
    """Contrast must remain an explicit positive numeric encoder setting."""
    with pytest.raises(ValueError, match="contrast"):
        ThermalRasterEncoder(contrast=contrast)  # type: ignore[arg-type]


@pytest.mark.parametrize("brightness", [0, -1, 1.5j, "brighter", True])
def test_encoder_rejects_invalid_brightness(brightness: object) -> None:
    """Brightness must remain an explicit positive numeric encoder setting."""
    with pytest.raises(ValueError, match="brightness"):
        ThermalRasterEncoder(brightness=brightness)  # type: ignore[arg-type]


@pytest.mark.parametrize("gamma", [0, -1, 1.5j, "lighter", True])
def test_encoder_rejects_invalid_gamma(gamma: object) -> None:
    """Gamma must remain an explicit positive numeric encoder setting."""
    with pytest.raises(ValueError, match="gamma"):
        ThermalRasterEncoder(gamma=gamma)  # type: ignore[arg-type]
