"""Exceptions raised by PiPrints imaging components."""


class ImagingError(RuntimeError):
    """Base class for errors raised by the imaging subsystem."""


class InvalidPhotoError(ImagingError):
    """Raised when a value cannot be used as a PiPrints photo."""


class InvalidAspectRatioError(ImagingError):
    """Raised when an aspect ratio has invalid dimensions."""


class InvalidCropError(ImagingError):
    """Raised when a crop region is invalid for a photo."""


class LayoutError(ImagingError):
    """Base class for layout-composition failures."""


class InvalidPhotoCountError(LayoutError):
    """Raised when a layout receives a different number of photos than required."""
