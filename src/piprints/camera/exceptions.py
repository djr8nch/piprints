"""Camera-specific exceptions."""


class CameraNotStartedError(RuntimeError):
    """Raised when a capture is requested before the camera is started."""
