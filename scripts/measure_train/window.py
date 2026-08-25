from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from .identity import Refused, RefusalCode

def parse_time(value: str|datetime)->datetime:
    dt=value if isinstance(value,datetime) else datetime.fromisoformat(value.replace("Z","+00:00"))
    if dt.tzinfo is None: raise Refused(RefusalCode.INVALID_WINDOW,"naive timestamp")
    return dt.astimezone(timezone.utc)

@dataclass(frozen=True)
class Window:
    since: datetime
    until: datetime
    def __post_init__(self):
        s=parse_time(self.since); u=parse_time(self.until)
        object.__setattr__(self,"since",s); object.__setattr__(self,"until",u)
        if not s < u: raise Refused(RefusalCode.INVALID_WINDOW,"since must precede until")
    def contains(self, when: str|datetime)->bool:
        t=parse_time(when); return self.since <= t < self.until
    @property
    def key(self): return f"[{self.since.isoformat()},{self.until.isoformat()})"
