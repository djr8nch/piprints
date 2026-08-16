"""Unit tests for timer-independent countdown progression."""

from __future__ import annotations

import pytest

from piprints.booth import Countdown


def test_countdown_progresses_to_capture_without_owning_a_clock() -> None:
    """A caller can schedule ticks without blocking the UI thread."""
    countdown = Countdown(3)

    assert countdown.start() == 3
    assert countdown.advance() == 2
    assert countdown.advance() == 1
    assert countdown.advance() is None
    assert countdown.remaining_seconds is None


def test_countdown_requires_start_before_advancing() -> None:
    """Invalid sequencing is detected at the countdown boundary."""
    with pytest.raises(RuntimeError, match="not been started"):
        Countdown(1).advance()


@pytest.mark.parametrize("duration", [0, -1, True, 1.5])
def test_countdown_rejects_invalid_duration(duration: object) -> None:
    """Countdown display duration is always a positive whole number."""
    with pytest.raises(ValueError, match="positive integer"):
        Countdown(duration)  # type: ignore[arg-type]
