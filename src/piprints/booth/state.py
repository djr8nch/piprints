"""Framework-independent lifecycle states for a PiPrints booth session."""

from enum import Enum, auto


class BoothState(Enum):
    """Describe the lifecycle of a booth session at the application boundary.

    The enum intentionally represents workflow concepts only.  Orchestration
    decides which transitions are currently supported; it is not a State
    pattern hierarchy.
    """

    IDLE = auto()
    PREPARING = auto()
    COUNTDOWN = auto()
    CAPTURING = auto()
    PROCESSING = auto()
    REVIEW = auto()
    COMPLETE = auto()
    ERROR = auto()
