from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from .subject import Subject
class DischargeResult(StrEnum): REQUALIFIED='REQUALIFIED'; BLOCKED='BLOCKED'; UNSUPPORTED='UNSUPPORTED'
@dataclass(frozen=True,slots=True)
class Delivery: event_id:str; consumer:Subject; delivered_at:datetime; receipt:str
@dataclass(frozen=True,slots=True)
class Acknowledgement: event_id:str; consumer:Subject; acknowledged_at:datetime; delivery_receipt:str
@dataclass(frozen=True,slots=True)
class Discharge: event_id:str; consumer:Subject; discharged_at:datetime; acknowledgement_receipt:str; result:DischargeResult; evidence_receipt:str
