"""Framework-independent events emitted by the booth workflow."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol
from uuid import UUID

from piprints.booth.state import BoothState
from piprints.imaging import Photo


class BoothEventType(Enum):
    """Meaningful occurrences exposed by the current booth workflow."""

    SESSION_STARTED = auto()
    STATE_CHANGED = auto()
    COUNTDOWN_TICK = auto()
    PHOTO_CAPTURED = auto()
    REVIEW_READY = auto()
    SESSION_COMPLETED = auto()
    ERROR = auto()


@dataclass(frozen=True, slots=True)
class BoothEvent:
    """Describe one booth occurrence without depending on a presentation layer."""

    event_type: BoothEventType
    state: BoothState
    session_id: UUID | None = None
    previous_state: BoothState | None = None
    countdown_value: int | None = None
    photo: Photo | None = None
    message: str | None = None


class BoothEventListener(Protocol):
    """Receive framework-independent booth workflow events."""

    def on_booth_event(self, event: BoothEvent) -> None:
        """Handle one event published by a booth workflow component."""
