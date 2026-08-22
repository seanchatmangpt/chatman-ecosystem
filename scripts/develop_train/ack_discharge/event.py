from dataclasses import dataclass
from datetime import datetime,timezone
from enum import StrEnum
from .subject import Subject
class InvalidationKind(StrEnum):
 NEW_HEAD='NEW_HEAD'; NEW_RECEIPT='NEW_RECEIPT'; SCHEMA_CHANGE='SCHEMA_CHANGE'; EXPIRED='EXPIRED'; BUILD_BROKEN='BUILD_BROKEN'; BLOCKED='BLOCKED'; RECOVERED='RECOVERED'
class RefusedEvent(ValueError): pass
@dataclass(frozen=True,slots=True)
class InvalidationEvent:
 producer:Subject; kind:InvalidationKind; event_id:str; occurred_at:datetime; replacement_receipt:str|None=None
 def __post_init__(self):
  if not self.event_id.strip(): raise RefusedEvent('REFUSED[EMPTY_INVALIDATION_EVENT]')
  if self.occurred_at.tzinfo is None: raise RefusedEvent('REFUSED[NAIVE_INVALIDATION_TIME]')
  if self.kind is InvalidationKind.NEW_RECEIPT and (not self.replacement_receipt or len(self.replacement_receipt)!=64): raise RefusedEvent('REFUSED[MISSING_REPLACEMENT_RECEIPT]')
 def timestamp(self): return self.occurred_at.astimezone(timezone.utc).isoformat()
