from dataclasses import dataclass
from .subject import Refused

@dataclass(frozen=True, order=True)
class Supersession:
    newer_id: str
    older_id: str
    reason: str

    def __post_init__(self):
        if not self.newer_id or not self.older_id or self.newer_id == self.older_id:
            raise Refused("REFUSED[INVALID_SUPERSESSION_EDGE]")
        if self.reason not in {"NEW_HEAD", "NEW_RUN", "NEW_ARTIFACT", "NEW_RECEIPT", "CORRECTION"}:
            raise Refused("REFUSED[INVALID_SUPERSESSION_REASON]")
