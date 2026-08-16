"""Tests for the Qt adapter around framework-independent booth events."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PySide6.QtWidgets import QApplication

from piprints.booth import BoothEvent, BoothEventType, BoothState
from piprints.imaging import Photo
from piprints.printing import PrintResult
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


def test_bridge_forwards_print_outcomes() -> None:
    """Print status remains an application event at the Qt boundary."""
    QApplication.instance() or QApplication(["piprints"])
    bridge = QtEventBridge()
    completed: list[PrintResult] = []
    failed: list[str] = []
    bridge.print_completed.connect(completed.append)
    bridge.print_failed.connect(failed.append)

    result = PrintResult(job_id="test-print")
    bridge.on_booth_event(
        BoothEvent(
            event_type=BoothEventType.PRINT_COMPLETED,
            state=BoothState.REVIEW,
            print_result=result,
        )
    )
    bridge.on_booth_event(
        BoothEvent(
            event_type=BoothEventType.PRINT_FAILED,
            state=BoothState.REVIEW,
            message="printer offline",
        )
    )

    assert completed == [result]
    assert failed == ["printer offline"]


def test_bridge_forwards_output_save_outcomes() -> None:
    """Save status remains a distinct application result from printing."""
    QApplication.instance() or QApplication(["piprints"])
    bridge = QtEventBridge()
    saved: list[object] = []
    failed: list[str] = []
    bridge.output_saved.connect(saved.append)
    bridge.output_save_failed.connect(failed.append)

    output_path = Path("/runtime/photos/final.png")
    bridge.on_booth_event(
        BoothEvent(
            event_type=BoothEventType.OUTPUT_SAVED,
            state=BoothState.REVIEW,
            output_path=output_path,
        )
    )
    bridge.on_booth_event(
        BoothEvent(
            event_type=BoothEventType.OUTPUT_SAVE_FAILED,
            state=BoothState.REVIEW,
            message="storage error",
        )
    )

    assert saved == [output_path]
    assert failed == ["storage error"]


def test_booth_package_does_not_depend_on_qt() -> None:
    """The framework adapter remains outside the booth/application boundary."""
    booth_directory = Path(__file__).parents[3] / "src" / "piprints" / "booth"

    for source_file in booth_directory.glob("*.py"):
        assert "PySide6" not in source_file.read_text(encoding="utf-8")
