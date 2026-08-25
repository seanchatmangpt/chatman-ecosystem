from .errors import Refused
def admit(subject, rows, now):
    seen={}; out=[]
    for r in rows:
        if r.subject!=subject: raise Refused("REFUSED[FOREIGN_SUBJECT]")
        if r.observed_at>now: raise Refused("REFUSED[FUTURE_EVIDENCE]")
        if r.case_id in seen and seen[r.case_id]!=r: raise Refused("REFUSED[CONTRADICTORY_DUPLICATE]")
        seen[r.case_id]=r; out.append(r)
    return tuple(sorted(set(out), key=lambda r:r.case_id))
