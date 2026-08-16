"""Tests for application-level dependency composition."""

from __future__ import annotations

import piprints.app as app
from tests.fakes import FakeCamera, FakePrinter


class _FakeApplication:
    """Avoid a real Qt event loop while exercising application composition."""

    def exec(self) -> int:
        """Return immediately after startup has been composed."""
        return 0


class _FakeWindow:
    """Record presentation startup without constructing Qt widgets."""

    def __init__(self) -> None:
        self.shown = False

    def show(self) -> None:
        """Record the normal startup display action."""
        self.shown = True


def test_main_injects_the_production_printer_into_the_booth(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    """Normal startup passes the bootstrap-configured printer to one booth."""
    camera = FakeCamera()
    printer = FakePrinter()
    window = _FakeWindow()
    received: dict[str, object] = {}
    monkeypatch.setattr(app, "create_application", _FakeApplication)
    monkeypatch.setattr(app, "create_camera", lambda: camera)
    monkeypatch.setattr(app, "create_event_bridge", object)
    monkeypatch.setattr(app, "create_production_printer", lambda: printer)
    monkeypatch.setattr(
        app,
        "create_booth",
        lambda configured_camera, **kwargs: received.update(
            camera=configured_camera, printer=kwargs["printer"]
        )
        or object(),
    )
    monkeypatch.setattr(app, "create_main_window", lambda *_args: window)

    assert app.main() == 0
    assert received == {"camera": camera, "printer": printer}
    assert camera.start_calls == 1
    assert camera.stop_calls == 1
    assert window.shown


def test_main_preserves_digital_only_startup_when_no_printer_is_configured(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    """The optional printer cannot prevent normal camera application startup."""
    camera = FakeCamera()
    received: dict[str, object] = {}
    monkeypatch.setattr(app, "create_application", _FakeApplication)
    monkeypatch.setattr(app, "create_camera", lambda: camera)
    monkeypatch.setattr(app, "create_event_bridge", object)
    monkeypatch.setattr(app, "create_production_printer", lambda: None)
    monkeypatch.setattr(
        app,
        "create_booth",
        lambda _camera, **kwargs: received.update(printer=kwargs["printer"])
        or object(),
    )
    monkeypatch.setattr(app, "create_main_window", lambda *_args: _FakeWindow())

    assert app.main() == 0
    assert received == {"printer": None}
    assert camera.start_calls == 1
    assert camera.stop_calls == 1
