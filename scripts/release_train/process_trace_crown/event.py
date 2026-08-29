from __future__ import annotations
from dataclasses import dataclass
from .refusal import Refused

@dataclass(frozen=True, order=True)
class Event:
    activity: str
    object_id: str
    lifecycle: str = "complete"

    def __post_init__(self) -> None:
        if not self.activity.strip():
            raise Refused("EMPTY_ACTIVITY")
        if not self.object_id.strip():
            raise Refused("EMPTY_OBJECT_ID")
        if self.lifecycle not in {"start", "complete", "suspend", "resume", "cancel"}:
            raise Refused("INVALID_LIFECYCLE", self.lifecycle)

    @property
    def activity_key(self) -> tuple[str, str]:
        return (self.activity, self.lifecycle)
