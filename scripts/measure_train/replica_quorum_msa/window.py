from dataclasses import dataclass
from datetime import datetime
from .subject import Refused
@dataclass(frozen=True)
class ObservationWindow:
    since:datetime; until:datetime
    def __post_init__(self):
        if self.since.tzinfo is None or self.until.tzinfo is None: raise Refused("REFUSED[NAIVE_WINDOW]")
        if self.until<=self.since: raise Refused("REFUSED[INVALID_WINDOW]")
    def admits(self,t): return self.since<=t<self.until
def admit_window(observations,window):
    return tuple(sorted(o for o in observations if window.admits(o.observed_at)))
