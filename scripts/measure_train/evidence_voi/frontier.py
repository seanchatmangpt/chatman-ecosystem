import hashlib, json
from .subject import Refused

def frontier_digest(candidates, calibrations):
    cal={c.candidate_id:c for c in calibrations}
    rows=[]
    for candidate in sorted(candidates):
        current=cal.get(candidate.candidate_id)
        if current is None:
            raise Refused("REFUSED[MISSING_CALIBRATION]")
        rows.append((candidate.candidate_id,current.generation,current.support,str(current.sensitivity),str(current.false_positive_rate)))
    raw=json.dumps(rows,separators=(",",":"))
    return hashlib.sha256(raw.encode()).hexdigest()

def admit_frontier(expected_digest, candidates, calibrations):
    current=frontier_digest(candidates,calibrations)
    if current != expected_digest:
        raise Refused("REFUSED[STALE_MEASUREMENT_FRONTIER]")
    return current
