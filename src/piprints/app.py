"""Application entry point for PiPrints."""

from __future__ import annotations

import logging

from piprints.bootstrap import create_application, create_main_window


def configure_logging() -> None:
    """Configure console logging for the application process."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    """Start the PiPrints application shell."""
    configure_logging()

    application = create_application()
    window = create_main_window()
    window.show()

    logging.getLogger(__name__).info("PiPrints application shell started")
    return application.exec()
