"""Basic package-level checks that do not require Raspberry Pi hardware."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from piprints import __version__
from piprints.bootstrap import create_application, create_main_window


def test_package_exposes_a_version() -> None:
    """Expose version metadata for callers and packaging tools."""
    assert __version__ == "0.1.0"


def test_application_shell_can_be_created() -> None:
    """Create the shell without requiring a display or Raspberry Pi hardware."""
    application = create_application(["piprints"])
    window = create_main_window()

    assert application is not None
    assert window.windowTitle() == "PiPrints"

    window.close()
