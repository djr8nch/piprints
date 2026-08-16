"""Practical shared dimensions for the 800 by 480 PiPrints touchscreen."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UiMetrics:
    """Dimensions used by the default touch-first presentation."""

    spacing_small: int = 8
    spacing_medium: int = 16
    spacing_large: int = 24
    screen_margin_horizontal: int = 28
    screen_margin_vertical: int = 24
    corner_radius: int = 16
    button_height: int = 72
    primary_button_height: int = 88
    body_text_size: int = 18
    title_text_size: int = 30
    hero_text_size: int = 44


METRICS = UiMetrics()
