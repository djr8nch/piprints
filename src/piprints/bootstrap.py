"""Composition root for the PiPrints application."""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

from PySide6.QtWidgets import QApplication

from piprints.booth import (
    BoothController,
    BoothEventListener,
    LayoutCatalog,
    LayoutOption,
)
from piprints.camera import Camera, PiCamera
from piprints.imaging import PhotoLoader, PhotoPipeline
from piprints.imaging.layouts import (
    ClassicPhotoStripLayout,
    FourPhotoLayout,
    SinglePhotoLayout,
)
from piprints.printing import Printer
from piprints.printing.thermal import (
    PrimuzThermalPrinter,
    ThermalRasterEncoder,
    UsbPrinterTransport,
)
from piprints.storage import FilesystemPhotoStorage, PhotoStorage
from piprints.themes import ThemeCatalog, ThemeOption
from piprints.ui import QtEventBridge
from piprints.ui.screens.main_window import MainWindow

_PRIMUZ_MC206H_PRINTABLE_WIDTH_DOTS = 384
_DEFAULT_PRIMUZ_USB_DEVICE_PATH = Path("/dev/usb/lp0")

logger = logging.getLogger(__name__)


def create_application(arguments: Sequence[str] | None = None) -> QApplication:
    """Create the Qt application shared by all PiPrints UI components."""
    existing_application = QApplication.instance()
    if existing_application is not None:
        return existing_application

    application_arguments = list(arguments) if arguments is not None else sys.argv
    return QApplication(application_arguments)


def create_camera() -> Camera:
    """Create the Raspberry Pi camera used by the application."""
    return PiCamera()


def create_photo_storage(output_directory: Path | None = None) -> PhotoStorage:
    """Create filesystem storage for completed digital booth photos."""
    return FilesystemPhotoStorage(output_directory or Path.cwd() / "photos")


def create_primuz_usb_printer(device_path: str | Path) -> Printer:
    """Create the validated USB transport wiring for a PRIMUZ MC206H.

    Callers supply the discovered Linux printer-class device path because it is
    system-specific; no hardware printer is created by default. The MC206H's
    384-dot printable width was physically validated with the USB raster path.
    """
    return PrimuzThermalPrinter(
        UsbPrinterTransport(device_path),
        ThermalRasterEncoder(
            max_width=_PRIMUZ_MC206H_PRINTABLE_WIDTH_DOTS,
            fit_to_max_width=True,
        ),
    )


def create_production_printer() -> Printer | None:
    """Create the configured PRIMUZ printer, or retain digital-only operation.

    The device path is temporary infrastructure composition for the validated
    Raspberry Pi setup. A future Configuration milestone will supply it rather
    than this bootstrap default.
    """
    if not _is_usable_printer_device(_DEFAULT_PRIMUZ_USB_DEVICE_PATH):
        return None
    return create_primuz_usb_printer(_DEFAULT_PRIMUZ_USB_DEVICE_PATH)


def _is_usable_printer_device(device_path: Path) -> bool:
    """Check whether this process can configure the known USB device path."""
    if not device_path.is_char_device():
        logger.info(
            "PRIMUZ printer is not configured: USB device %s is unavailable.",
            device_path,
        )
        return False
    if not os.access(device_path, os.W_OK):
        logger.warning(
            "PRIMUZ printer is not configured: current user cannot write %s.",
            device_path,
        )
        return False
    return True


def create_layout_catalog() -> LayoutCatalog:
    """Create the currently supported user-selectable layout catalog."""
    options = (
        LayoutOption("single", "Single Photo", "1 photo", 1, 1, 1),
        LayoutOption("grid", "Four Photo Grid", "4 photos", 4, 2, 2),
        LayoutOption("strip", "Classic Strip", "4 photos", 4, 1, 4),
    )
    return LayoutCatalog(
        options,
        {
            "single": SinglePhotoLayout,
            "grid": FourPhotoLayout,
            "strip": ClassicPhotoStripLayout,
        },
    )


def create_theme_catalog() -> ThemeCatalog:
    """Create the theme choices currently usable by the application.

    The neutral PiPrints presentation is the sole available theme today. A
    future Themes & Branding milestone may add rendering strategies and assets
    behind this metadata boundary without changing selection widgets.
    """
    return ThemeCatalog((ThemeOption("default", "PiPrints"),))


def create_booth(
    camera: Camera,
    capture_directory: Path | None = None,
    photo_storage: PhotoStorage | None = None,
    printer: Printer | None = None,
    listeners: Iterable[BoothEventListener] = (),
) -> BoothController:
    """Create the booth workflow with its runtime capture location."""
    directory = capture_directory or Path.cwd() / "captures"
    return BoothController(
        camera=camera,
        capture_directory=directory,
        photo_loader=PhotoLoader(),
        photo_pipeline=PhotoPipeline(),
        layout=FourPhotoLayout(),
        layout_catalog=create_layout_catalog(),
        theme_catalog=create_theme_catalog(),
        photo_storage=photo_storage or create_photo_storage(),
        printer=printer,
        listeners=listeners,
    )


def create_event_bridge() -> QtEventBridge:
    """Create the Qt adapter for booth events at the presentation boundary."""
    return QtEventBridge()


def create_main_window(
    camera: Camera,
    booth: BoothController,
    event_bridge: QtEventBridge,
) -> MainWindow:
    """Create the main window with its camera dependency.

    Camera construction remains in this composition root so UI code depends on
    the PiPrints camera contract rather than hardware implementations.
    """
    return MainWindow(camera, booth, event_bridge)
