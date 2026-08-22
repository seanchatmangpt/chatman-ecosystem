from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused

@dataclass(frozen=True, order=True)
class Acknowledgement:
    event_id: str
    consumer: Subject
    delivery_id: str
    acknowledged_at: datetime
    ack_id: str

    def __post_init__(self):
        if not self.event_id.strip() or not self.delivery_id.strip() or not self.ack_id.strip():
            raise Refused("REFUSED[INVALID_ACK_IDENTITY]")
        if self.acknowledged_at.tzinfo is None or self.acknowledged_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_ACK_TIME]")
