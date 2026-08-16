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
    output_saved = Signal(object)
    output_save_failed = Signal(str)
    print_completed = Signal(object)
    print_failed = Signal(str)
    review_ready = Signal(object)
    error_occurred = Signal(str)
    error_presented = Signal(object)

    def on_booth_event(self, event: BoothEvent) -> None:
        """Translate one supported application event into a Qt signal."""
        match event.event_type:
            case BoothEventType.STATE_CHANGED:
                if event.previous_state is not None:
                    self.state_changed.emit(event.previous_state, event.state)
            case BoothEventType.COUNTDOWN_TICK:
                if event.countdown_value is not None:
                    self.countdown_tick.emit(event.countdown_value)
            case BoothEventType.OUTPUT_SAVED:
                if event.output_path is not None:
                    self.output_saved.emit(event.output_path)
            case BoothEventType.OUTPUT_SAVE_FAILED:
                self.output_save_failed.emit(
                    event.message or "Unable to save the photo."
                )
            case BoothEventType.PRINT_COMPLETED:
                if event.print_result is not None:
                    self.print_completed.emit(event.print_result)
            case BoothEventType.PRINT_FAILED:
                self.print_failed.emit(event.message or "Unable to print the photo.")
            case BoothEventType.REVIEW_READY:
                if event.photo is not None:
                    self.review_ready.emit(event.photo)
            case BoothEventType.ERROR:
                self.error_presented.emit(event)
                self.error_occurred.emit(
                    event.message or "An unexpected booth error occurred."
                )
