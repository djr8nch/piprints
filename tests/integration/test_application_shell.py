"""Integration smoke tests for application bootstrap and main-window wiring."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from piprints.bootstrap import (
    create_application,
    create_booth,
    create_event_bridge,
    create_main_window,
)
from tests.fakes import FakeCamera


def test_application_shell_can_be_created(tmp_path: Path) -> None:
    """Compose the Qt application, booth workflow, and main window with a fake."""
    application = create_application(["piprints"])
    camera = FakeCamera()
    event_bridge = create_event_bridge()
    booth = create_booth(camera, tmp_path / "captures", listeners=[event_bridge])
    window = create_main_window(camera, booth, event_bridge)

    assert application is not None
    assert window.windowTitle() == "PiPrints"

    window.close()
