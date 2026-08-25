from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class Freshness:
    max_age_seconds:float
    def current(self,observed_at,now):
        if observed_at.tzinfo is None or now.tzinfo is None: raise Refused("NAIVE_TIME")
        age=(now-observed_at).total_seconds()
        if age<0: raise Refused("FUTURE_OBSERVATION")
        return age<=self.max_age_seconds
