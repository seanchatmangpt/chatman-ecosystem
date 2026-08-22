from .evidence_axis import Outcome
def classify(left, right):
    if left.subject != right.subject:
        return "REFUSED[FOREIGN_SUBJECT]"
    lm={r.axis:r.outcome for r in left.rows}; rm={r.axis:r.outcome for r in right.rows}
    shared=set(lm)&set(rm)
    if not shared: return "UNKNOWN"
    if any(lm[a] != rm[a] for a in shared): return "DIVERGED"
    return "COMPATIBLE"
def standing(vector):
    vals=[r.outcome for r in vector.rows]
    if not vals or Outcome.UNKNOWN in vals or Outcome.PENDING in vals: return "UNKNOWN"
    if Outcome.FAIL in vals: return "BUILD_BROKEN"
    if all(v is Outcome.UNSUPPORTED for v in vals): return "UNSUPPORTED"
    return "PARTIAL_ALIVE"
