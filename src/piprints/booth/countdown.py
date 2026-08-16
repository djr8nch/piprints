"""Timer-independent countdown progression for the booth workflow."""

from __future__ import annotations


class Countdown:
    """Track discrete countdown ticks without owning a clock or a UI."""

    def __init__(self, duration_seconds: int) -> None:
        if (
            isinstance(duration_seconds, bool)
            or not isinstance(duration_seconds, int)
            or duration_seconds <= 0
        ):
            raise ValueError("Countdown duration must be a positive integer.")
        self._duration_seconds = duration_seconds
        self._remaining_seconds: int | None = None

    @property
    def remaining_seconds(self) -> int | None:
        """Return the current displayed value, or ``None`` before start/end."""
        return self._remaining_seconds

    def start(self) -> int:
        """Start the countdown and return its initial display value."""
        self._remaining_seconds = self._duration_seconds
        return self._remaining_seconds

    def advance(self) -> int | None:
        """Advance one tick, returning ``None`` when capture should begin."""
        if self._remaining_seconds is None:
            raise RuntimeError("Countdown has not been started.")
        self._remaining_seconds -= 1
        if self._remaining_seconds == 0:
            self._remaining_seconds = None
            return None
        return self._remaining_seconds
