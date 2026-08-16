"""Tests for the booth lifecycle state contract."""

from piprints.booth import BoothState


def test_booth_states_define_the_session_lifecycle_contract() -> None:
    """The workflow vocabulary stays explicit and predictably ordered."""
    assert tuple(state.name for state in BoothState) == (
        "IDLE",
        "PREPARING",
        "COUNTDOWN",
        "CAPTURING",
        "PROCESSING",
        "REVIEW",
        "COMPLETE",
        "ERROR",
    )
