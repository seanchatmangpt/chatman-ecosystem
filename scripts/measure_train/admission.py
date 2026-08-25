from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from .identity import Subject, Refused, RefusalCode
from .evidence import Evidence
from .window import Window, parse_time

@dataclass(frozen=True)
class AdmissionResult:
    admitted: tuple[Evidence,...]
    excluded_out_of_window: int

def admit(subject: Subject, rows: list[Evidence], window: Window, now: datetime, max_age: timedelta)->AdmissionResult:
    now=parse_time(now); by_id={}; admitted=[]; excluded=0
    for row in rows:
        if row.subject != subject: raise Refused(RefusalCode.STALE_OR_FOREIGN_SUBJECT,row.subject.identity)
        if row.observed_at > now: raise Refused(RefusalCode.EVIDENCE_FUTURE,row.source_id)
        if now-row.observed_at > max_age: raise Refused(RefusalCode.EVIDENCE_STALE,row.source_id)
        if not window.contains(row.observed_at): excluded += 1; continue
        key=(row.kind,row.source_id)
        prev=by_id.get(key)
        if prev and prev != row: raise Refused(RefusalCode.CONFLICTING_EVIDENCE,row.source_id)
        if not prev: by_id[key]=row; admitted.append(row)
    return AdmissionResult(tuple(sorted(admitted,key=lambda x:(x.kind,x.source_id))),excluded)
