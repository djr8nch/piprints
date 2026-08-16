"""Application-level layout choices and factories for booth sessions."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from piprints.imaging.layouts import Layout


@dataclass(frozen=True, slots=True)
class LayoutOption:
    """Describe one selectable layout without exposing its implementation."""

    identifier: str
    name: str
    description: str
    required_photos: int
    preview_columns: int
    preview_rows: int

    def __post_init__(self) -> None:
        """Reject descriptors that cannot be rendered or used in a session."""
        if not self.identifier or not self.name or not self.description:
            raise ValueError(
                "A layout option requires an identifier, name, and description."
            )
        if self.required_photos <= 0:
            raise ValueError("A layout option must require at least one photo.")
        if self.preview_columns <= 0 or self.preview_rows <= 0:
            raise ValueError(
                "A layout preview must have positive row and column counts."
            )


class LayoutCatalog:
    """Expose supported layout descriptors and create their selected strategy."""

    def __init__(
        self,
        options: tuple[LayoutOption, ...],
        factories: Mapping[str, Callable[[], Layout]],
    ) -> None:
        if not options:
            raise ValueError("A layout catalog requires at least one option.")
        option_ids = {option.identifier for option in options}
        if len(option_ids) != len(options):
            raise ValueError("Layout option identifiers must be unique.")
        if option_ids != set(factories):
            raise ValueError("Every layout option requires exactly one factory.")
        self._options = options
        self._factories = dict(factories)

    @property
    def options(self) -> tuple[LayoutOption, ...]:
        """Return the selectable layouts in presentation order."""
        return self._options

    @property
    def default_identifier(self) -> str:
        """Return the first configured layout's identifier."""
        return self._options[0].identifier

    def create(self, identifier: str) -> Layout:
        """Create the requested strategy after validating its declared capture count."""
        try:
            option = next(
                item for item in self._options if item.identifier == identifier
            )
        except StopIteration as error:
            raise ValueError(f"Unsupported layout: {identifier!r}.") from error
        layout = self._factories[identifier]()
        if layout.required_photos != option.required_photos:
            raise ValueError(
                f"Layout {identifier!r} requires {layout.required_photos} photos, "
                f"not the configured {option.required_photos}."
            )
        return layout
