from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused

RESULTS={"REQUALIFIED","BLOCKED","UNSUPPORTED"}

@dataclass(frozen=True, order=True)
class Discharge:
    event_id: str
    consumer: Subject
    ack_id: str
    result: str
    verified_at: datetime
    proof_id: str

    def __post_init__(self):
        if self.result not in RESULTS:
            raise Refused("REFUSED[INVALID_DISCHARGE_RESULT]")
        if not self.event_id.strip() or not self.ack_id.strip() or not self.proof_id.strip():
            raise Refused("REFUSED[INVALID_DISCHARGE_IDENTITY]")
        if self.verified_at.tzinfo is None or self.verified_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_DISCHARGE_TIME]")
