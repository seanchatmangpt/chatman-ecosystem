from dataclasses import dataclass
from .subject import Refused

STATES = {"UNKNOWN","PENDING","PASS","FAIL","UNSUPPORTED","REFUSED"}
REQUIRED_KINDS = {
    "METHODOLOGY","POWL","REACTOR","PROJECTION","DISTRIBUTED",
    "REPLAY","BRCE","CI","ARTIFACT","REFERENCE_ORACLE"
}

@dataclass(frozen=True, order=True)
class Obligation:
    obligation_id: str
    kind: str
    required: bool = True

    def __post_init__(self):
        if not self.obligation_id.strip():
            raise Refused("REFUSED[EMPTY_OBLIGATION_ID]")
        if self.kind not in REQUIRED_KINDS:
            raise Refused("REFUSED[UNKNOWN_OBLIGATION_KIND]")
