from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .model import Refused


def _parse(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise Refused("INVALID_TIMESTAMP", value) from exc
    if parsed.tzinfo is None:
        raise Refused("NAIVE_TIMESTAMP", value)
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class ObservationWindow:
    start: str
    end: str

    def __post_init__(self) -> None:
        if _parse(self.start) >= _parse(self.end):
            raise Refused("INVALID_WINDOW", f"{self.start}..{self.end}")

    def admits(self, observed_at: str) -> bool:
        instant = _parse(observed_at)
        return _parse(self.start) <= instant < _parse(self.end)

    def require(self, observed_at: str) -> None:
        if not self.admits(observed_at):
            raise Refused("OUTSIDE_OBSERVATION_WINDOW", observed_at)
