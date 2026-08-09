"""State values for the initial PiPrints booth workflow."""

from enum import Enum, auto


class BoothState(Enum):
    """The small set of states required for basic booth capture."""

    IDLE = auto()
    COUNTDOWN = auto()
    CAPTURING = auto()
    REVIEW = auto()
