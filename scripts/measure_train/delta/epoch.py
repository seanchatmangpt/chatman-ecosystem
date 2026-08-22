from dataclasses import dataclass
from datetime import datetime, timezone
@dataclass(frozen=True)
class Epoch:
    observed_at:datetime
    def __post_init__(self):
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("REFUSED[NAIVE_EPOCH]")
    def age_seconds(self, now:datetime)->float:
        if now.tzinfo is None or now.utcoffset() is None: raise ValueError("REFUSED[NAIVE_NOW]")
        return (now.astimezone(timezone.utc)-self.observed_at.astimezone(timezone.utc)).total_seconds()
