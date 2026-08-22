from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused

@dataclass(frozen=True, order=True)
class Delivery:
    event_id: str
    consumer: Subject
    delivered_at: datetime
    delivery_id: str

    def __post_init__(self):
        if not self.event_id.strip() or not self.delivery_id.strip():
            raise Refused("REFUSED[INVALID_DELIVERY_IDENTITY]")
        if self.delivered_at.tzinfo is None or self.delivered_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_DELIVERY_TIME]")
