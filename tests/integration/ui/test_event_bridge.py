"""Tests for the Qt adapter around framework-independent booth events."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PySide6.QtWidgets import QApplication

from piprints.booth import BoothEvent, BoothEventType, BoothState
from piprints.imaging import Photo
from piprints.ui import QtEventBridge


def test_bridge_preserves_state_transition_data() -> None:
    """State signals retain both states from the application event."""
    QApplication.instance() or QApplication(["piprints"])
    bridge = QtEventBridge()
    received: list[tuple[BoothState, BoothState]] = []
    bridge.state_changed.connect(
        lambda previous, current: received.append((previous, current))
    )

    bridge.on_booth_event(
        BoothEvent(
            event_type=BoothEventType.STATE_CHANGED,
            previous_state=BoothState.PREPARING,
            state=BoothState.COUNTDOWN,
        )
    )

    assert received == [(BoothState.PREPARING, BoothState.COUNTDOWN)]


def test_bridge_preserves_countdown_values() -> None:
    """Countdown signals retain the controller-provided value."""
    QApplication.instance() or QApplication(["piprints"])
    bridge = QtEventBridge()
    received: list[int] = []
    bridge.countdown_tick.connect(received.append)

    bridge.on_booth_event(
        BoothEvent(
            event_type=BoothEventType.COUNTDOWN_TICK,
            state=BoothState.COUNTDOWN,
            countdown_value=2,
        )
    )

    assert received == [2]


def test_bridge_surfaces_booth_error_messages() -> None:
    """Error signals expose the diagnostic information supplied by the booth."""
    QApplication.instance() or QApplication(["piprints"])
    bridge = QtEventBridge()
    received: list[str] = []
    bridge.error_occurred.connect(received.append)

    bridge.on_booth_event(
        BoothEvent(
            event_type=BoothEventType.ERROR,
            state=BoothState.ERROR,
            message="camera disconnected",
        )
    )

    assert received == ["camera disconnected"]


def test_bridge_preserves_review_ready_photo() -> None:
    """The UI receives the exact final photo selected by the workflow."""
    QApplication.instance() or QApplication(["piprints"])
    bridge = QtEventBridge()
    photo = Photo(Image.new("RGB", (2, 3), "red"))
    received: list[Photo] = []
    bridge.review_ready.connect(received.append)

    bridge.on_booth_event(
        BoothEvent(
            event_type=BoothEventType.REVIEW_READY,
            state=BoothState.REVIEW,
            photo=photo,
        )
    )

    assert received == [photo]


def test_booth_package_does_not_depend_on_qt() -> None:
    """The framework adapter remains outside the booth/application boundary."""
    booth_directory = Path(__file__).parents[3] / "src" / "piprints" / "booth"

    for source_file in booth_directory.glob("*.py"):
        assert "PySide6" not in source_file.read_text(encoding="utf-8")
