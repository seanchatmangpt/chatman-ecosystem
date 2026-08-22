from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from .identity import Subject, Standing
from .window import Window
from .evidence import Evidence
from .admission import admit
from .census import Census, census
from .invalidation import detect_invalidations, Invalidation
from .receipts import Receipt, manufacture
from .telemetry import ProcessEvent, project_ocel

@dataclass(frozen=True)
class Measurement:
    subject: Subject
    census: Census
    receipt: Receipt
    events: tuple[ProcessEvent,...]
    invalidations: tuple[Invalidation,...]
    excluded_out_of_window: int
    authority: str='OBSERVE_MEASURE_ONLY'
    @property
    def standing(self)->Standing:
        return Standing.UNKNOWN if self.invalidations else self.census.standing

def measure(subject: Subject, rows: list[Evidence], window: Window, now: datetime, max_age: timedelta, ttl_by_kind: dict[str,timedelta]|None=None)->Measurement:
    a=admit(subject,rows,window,now,max_age); c=census(a.admitted); inv=detect_invalidations(a.admitted,now,ttl_by_kind or {})
    receipt=manufacture(subject.identity,a.admitted)
    return Measurement(subject,c,receipt,project_ocel(a.admitted),inv,a.excluded_out_of_window)
