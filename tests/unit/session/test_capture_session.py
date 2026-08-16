"""Unit tests for the capture-session domain model."""

from __future__ import annotations

import pytest
from PIL import Image

from piprints.imaging import Photo
from piprints.session import CaptureSession, CaptureSessionError


def make_photo() -> Photo:
    """Create a minimal valid photo for session tests."""
    return Photo(Image.new("RGB", (1, 1), "black"))


@pytest.mark.parametrize("target", [0, -1, True, 1.5])
def test_session_rejects_invalid_target_count(target: object) -> None:
    """A session always requires a positive integer number of captures."""
    with pytest.raises(CaptureSessionError, match="positive integer"):
        CaptureSession(target)  # type: ignore[arg-type]


def test_session_tracks_progress_and_exposes_an_immutable_photo_snapshot() -> None:
    """The session is the source of truth for ordered capture progress."""
    session = CaptureSession(2)
    first_photo = make_photo()
    session.add_photo(first_photo)

    assert session.photos == (first_photo,)
    assert session.photo_count == 1
    assert session.remaining_photos == 1
    assert not session.is_complete

    session.add_photo(make_photo())

    assert session.photo_count == 2
    assert session.remaining_photos == 0
    assert session.is_complete


def test_session_rejects_photo_beyond_configured_target() -> None:
    """Overflow is explicit rather than silently discarded or accepted."""
    session = CaptureSession(1)
    session.add_photo(make_photo())

    with pytest.raises(CaptureSessionError, match="complete capture session"):
        session.add_photo(make_photo())
