"""Application entry point for PiPrints."""

from __future__ import annotations

import logging

from piprints.bootstrap import (
    create_application,
    create_booth,
    create_camera,
    create_event_bridge,
    create_main_window,
)


def configure_logging() -> None:
    """Configure console logging for the application process."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    """Start the PiPrints live camera preview application."""
    configure_logging()

    application = create_application()
    camera = create_camera()
    event_bridge = create_event_bridge()
    booth = create_booth(camera, listeners=[event_bridge])
    try:
        camera.start()
    except Exception:
        logging.getLogger(__name__).exception("PiPrints could not start the camera")
        camera.stop()
        return 1

    window = create_main_window(camera, booth, event_bridge)
    window.show()

    logging.getLogger(__name__).info("PiPrints camera preview started")
    try:
        return application.exec()
    finally:
        camera.stop()
