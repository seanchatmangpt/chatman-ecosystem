from dataclasses import dataclass
from datetime import datetime, timezone
class EpochRefusal(ValueError): pass
@dataclass(frozen=True)
class Epoch:
    since: datetime
    until: datetime
    def __post_init__(self):
        if self.since.tzinfo is None or self.until.tzinfo is None: raise EpochRefusal("REFUSED[NAIVE_EPOCH]")
        s=self.since.astimezone(timezone.utc); u=self.until.astimezone(timezone.utc)
        if not s < u: raise EpochRefusal("REFUSED[INVALID_EPOCH]")
        object.__setattr__(self,"since",s); object.__setattr__(self,"until",u)
    def contains(self, instant):
        if instant.tzinfo is None: raise EpochRefusal("REFUSED[NAIVE_OBSERVATION]")
        t=instant.astimezone(timezone.utc)
        return self.since <= t < self.until
