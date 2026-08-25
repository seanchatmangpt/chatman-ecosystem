from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from .event import Event
from .refusal import Refused
from .subject import Subject

@dataclass(frozen=True)
class Trace:
    subject: Subject
    engine: str
    events: tuple[Event, ...]

    def __post_init__(self) -> None:
        if not self.engine.strip():
            raise Refused("EMPTY_ENGINE")
        if not self.events:
            raise Refused("EMPTY_TRACE")

    @property
    def digest(self) -> str:
        body = {"subject": self.subject.key, "engine": self.engine, "events": [e.__dict__ for e in self.events]}
        return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
