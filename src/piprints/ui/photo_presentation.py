"""Focused conversion of PiPrints photos for Qt presentation."""

from __future__ import annotations

from PySide6.QtGui import QImage, QPixmap

from piprints.imaging import Photo


def photo_to_pixmap(photo: Photo) -> QPixmap:
    """Create an independent Qt pixmap from an RGB imaging-domain photo."""
    image = photo.image
    qt_image = QImage(
        image.tobytes(),
        image.width,
        image.height,
        image.width * 3,
        QImage.Format.Format_RGB888,
    ).copy()
    return QPixmap.fromImage(qt_image)
