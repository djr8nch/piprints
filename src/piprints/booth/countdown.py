"""Framework-independent countdown execution for booth workflows."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from time import sleep

Delay = Callable[[float], None]


class Countdown:
    """Execute a countdown and yield display-ready ticks in descending order."""

    def __init__(self, duration_seconds: int, delay: Delay = sleep) -> None:
        if (
            isinstance(duration_seconds, bool)
            or not isinstance(duration_seconds, int)
            or duration_seconds <= 0
        ):
            raise ValueError("Countdown duration must be a positive integer.")
        self._duration_seconds = duration_seconds
        self._delay = delay

    @property
    def duration_seconds(self) -> int:
        """Return the configured duration and number of countdown ticks."""
        return self._duration_seconds

    def ticks(self) -> Iterator[int]:
        """Yield each countdown value after holding it for one second.

        The injected delay keeps production timing simple while allowing unit
        tests and alternate application hosts to execute deterministically.
        """
        for remaining_seconds in range(self._duration_seconds, 0, -1):
            yield remaining_seconds
            self._delay(1)
