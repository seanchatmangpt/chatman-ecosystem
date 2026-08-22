from dataclasses import dataclass
from datetime import datetime, timezone

def _utc(v):
    if v.tzinfo is None: raise ValueError("REFUSED[NAIVE_TIME]")
    return v.astimezone(timezone.utc)

@dataclass(frozen=True)
class EvaluationWindow:
    start: datetime
    end: datetime
    def __post_init__(self):
        s,e=_utc(self.start),_utc(self.end)
        if not s < e: raise ValueError("REFUSED[INVALID_WINDOW]")
        object.__setattr__(self,"start",s); object.__setattr__(self,"end",e)
    def contains(self, instant):
        t=_utc(instant); return self.start <= t < self.end
