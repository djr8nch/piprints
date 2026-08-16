"""Unit tests for timer-independent countdown progression."""

from __future__ import annotations

import pytest

from piprints.booth import Countdown


def test_countdown_yields_ticks_in_order_without_waiting_in_tests() -> None:
    """A fake delay makes countdown execution deterministic and immediate."""
    delays: list[float] = []
    countdown = Countdown(3, delay=delays.append)

    assert tuple(countdown.ticks()) == (3, 2, 1)
    assert delays == [1, 1, 1]


def test_countdown_uses_its_configured_duration() -> None:
    """The number of ticks comes from the configured booth duration."""
    countdown = Countdown(2, delay=lambda _: None)

    assert countdown.duration_seconds == 2
    assert tuple(countdown.ticks()) == (2, 1)


@pytest.mark.parametrize("duration", [0, -1, True, 1.5])
def test_countdown_rejects_invalid_duration(duration: object) -> None:
    """Countdown display duration is always a positive whole number."""
    with pytest.raises(ValueError, match="positive integer"):
        Countdown(duration)  # type: ignore[arg-type]
