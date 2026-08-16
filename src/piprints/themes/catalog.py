"""Application-owned metadata for selectable booth themes.

This module intentionally describes selection choices only. Theme rendering,
overlays, watermarks, typography, and colour systems belong to the separate
Themes & Branding milestone.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ThemeOption:
    """Describe one theme that is currently usable by the application."""

    identifier: str
    name: str
    preview_path: Path | None = None
    available: bool = True

    def __post_init__(self) -> None:
        """Reject incomplete descriptors before they reach the UI."""
        if not self.identifier or not self.name:
            raise ValueError("A theme option requires an identifier and name.")


class ThemeCatalog:
    """Expose usable theme metadata without defining how themes are rendered."""

    def __init__(self, options: tuple[ThemeOption, ...]) -> None:
        identifiers = [option.identifier for option in options]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Theme option identifiers must be unique.")
        self._options = tuple(option for option in options if option.available)
        if not self._options:
            raise ValueError("A theme catalog requires at least one usable theme.")

    @property
    def options(self) -> tuple[ThemeOption, ...]:
        """Return usable themes in presentation order."""
        return self._options

    @property
    def default_identifier(self) -> str:
        """Return the configured default usable theme identifier."""
        return self._options[0].identifier

    def contains(self, identifier: str) -> bool:
        """Return whether an identifier names a currently usable theme."""
        return any(option.identifier == identifier for option in self._options)
