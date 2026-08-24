from .refusals import Refused
def admit(subject,rows,now):
    rows=tuple(rows)
    if not rows: raise Refused('REFUSED[EMPTY_TRAJECTORY]')
    seen=set(); prev=None
    for r in rows:
        if r.subject.repo!=subject.repo or r.subject.semantic_digest!=subject.semantic_digest: raise Refused('REFUSED[FOREIGN_SEMANTIC_SUBJECT]')
        if r.observed_at>now: raise Refused('REFUSED[FUTURE_EVIDENCE]')
        if r.observation_id in seen: raise Refused('REFUSED[DUPLICATE_OBSERVATION]')
        seen.add(r.observation_id)
        if prev is not None:
            if r.subject.generation!=prev.subject.generation+1: raise Refused('REFUSED[TORN_GENERATION_TRAJECTORY]')
            if r.observed_at<=prev.observed_at: raise Refused('REFUSED[NON_MONOTONE_TIME]')
        prev=r
    if rows[-1].subject!=subject: raise Refused('REFUSED[STALE_TRAJECTORY_HEAD]')
    return rows
