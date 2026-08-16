"""Qt presentation adapter for framework-independent booth lifecycle events."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from piprints.booth import BoothEvent, BoothEventType


class QtEventBridge(QObject):
    """Translate selected ``BoothEvent`` values into Qt presentation signals.

    The bridge is a ``BoothEventListener`` implemented at the UI boundary.  It
    intentionally contains no booth commands or workflow decisions: its only
    responsibility is forwarding application event data through Qt's
    thread-safe signal delivery mechanism.
    """

    state_changed = Signal(object, object)
    countdown_tick = Signal(int)
    review_ready = Signal(object)
    error_occurred = Signal(str)

    def on_booth_event(self, event: BoothEvent) -> None:
        """Translate one supported application event into a Qt signal."""
        match event.event_type:
            case BoothEventType.STATE_CHANGED:
                if event.previous_state is not None:
                    self.state_changed.emit(event.previous_state, event.state)
            case BoothEventType.COUNTDOWN_TICK:
                if event.countdown_value is not None:
                    self.countdown_tick.emit(event.countdown_value)
            case BoothEventType.REVIEW_READY:
                if event.photo is not None:
                    self.review_ready.emit(event.photo)
            case BoothEventType.ERROR:
                self.error_occurred.emit(
                    event.message or "An unexpected booth error occurred."
                )
