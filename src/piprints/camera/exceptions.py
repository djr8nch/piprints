"""Camera-specific exceptions."""


class CameraNotStartedError(RuntimeError):
    """Raised when a capture is requested before the camera is started."""


class CameraPreviewError(RuntimeError):
    """Raised when a camera frame cannot be prepared for preview."""


class CameraStartupError(RuntimeError):
    """Raised when the Raspberry Pi camera cannot be started."""
