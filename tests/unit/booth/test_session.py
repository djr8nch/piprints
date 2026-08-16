"""Tests for the booth-session artifact model."""

from uuid import UUID

import pytest
from PIL import Image

from piprints.booth import BoothSession, BoothSessionError
from piprints.imaging import Photo


def make_photo(color: str) -> Photo:
    """Create a small in-memory photo for a session test."""
    return Photo(Image.new("RGB", (1, 1), color))


def test_session_initializes_with_a_unique_identifier() -> None:
    """Each newly created interaction can be identified independently."""
    first_session = BoothSession()
    second_session = BoothSession()

    assert isinstance(first_session.id, UUID)
    assert first_session.id != second_session.id
    assert first_session.captured_photos == ()
    assert first_session.photo_count == 0
    assert first_session.final_photo is None


def test_session_accepts_an_explicit_identifier() -> None:
    """Callers can construct deterministic sessions where identity matters."""
    session_id = UUID("12345678-1234-5678-1234-567812345678")

    session = BoothSession(session_id=session_id)

    assert session.id is session_id


def test_session_preserves_capture_order_and_hides_its_collection() -> None:
    """One model supports both single- and multi-photo capture sequences."""
    session = BoothSession(target_photo_count=2)
    first_photo = make_photo("red")
    second_photo = make_photo("blue")

    session.add_captured_photo(first_photo)
    session.add_captured_photo(second_photo)

    captured_photos = session.captured_photos

    assert captured_photos == (first_photo, second_photo)
    assert session.photo_count == 2
    with pytest.raises(AttributeError):
        captured_photos.append(make_photo("green"))  # type: ignore[attr-defined]
    assert session.captured_photos == (first_photo, second_photo)


def test_session_records_one_final_photo_after_capture() -> None:
    """A composed output belongs to the session that supplied its captures."""
    session = BoothSession()
    captured_photo = make_photo("red")
    final_photo = make_photo("blue")
    session.add_captured_photo(captured_photo)

    session.set_final_photo(final_photo)

    assert session.final_photo is final_photo
    with pytest.raises(BoothSessionError, match="already been assigned"):
        session.set_final_photo(make_photo("green"))
    with pytest.raises(BoothSessionError, match="after assigning"):
        session.add_captured_photo(make_photo("yellow"))


def test_session_rejects_a_final_photo_without_any_captures() -> None:
    """A final output cannot exist without source session artifacts."""
    session = BoothSession()

    with pytest.raises(BoothSessionError, match="all required photos"):
        session.set_final_photo(make_photo("red"))
