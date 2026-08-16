"""Semantic color tokens for the current default PiPrints identity."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColorPalette:
    """Accessible semantic colors used by the shared Qt stylesheet."""

    brand_pink: str = "#FFE3FB"
    brand_mint: str = "#E6EFD7"
    background: str = "#FAFAF8"
    surface: str = "#FFFFFF"
    surface_subtle: str = "#F3F4F0"
    text_primary: str = "#252525"
    text_secondary: str = "#5D625B"
    border: str = "#D7DAD2"
    disabled_surface: str = "#E4E6E1"
    disabled_text: str = "#767A73"
    focus: str = "#4C7A67"
    pressed_mint: str = "#D5E4BE"
    pressed_pink: str = "#F4CDEF"
    accent_border: str = "#C789B8"
    success_surface: str = "#E6EFD7"
    success_text: str = "#355126"
    error_surface: str = "#FDE8E7"
    error_text: str = "#9B2521"
    error_border: str = "#D75B55"
    overlay: str = "rgba(0, 0, 0, 145)"
    preview_background: str = "#101010"


PALETTE = ColorPalette()
