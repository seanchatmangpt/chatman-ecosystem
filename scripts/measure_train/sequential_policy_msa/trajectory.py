from .refusal import Refused

def admit_trajectory(subject, policy, steps):
    ordered=tuple(sorted(steps,key=lambda s:s.step))
    seen=set()
    for i,s in enumerate(ordered):
        if s.subject != subject:
            raise Refused("REFUSED[FOREIGN_SUBJECT]")
        if s.policy != policy:
            raise Refused("REFUSED[FOREIGN_POLICY]")
        if s.step != i:
            raise Refused("REFUSED[NONCONTIGUOUS_TRAJECTORY]")
        if s.evidence_id in seen:
            raise Refused("REFUSED[DUPLICATE_EVIDENCE]")
        seen.add(s.evidence_id)
        if i and s.observed_at < ordered[i-1].observed_at:
            raise Refused("REFUSED[TIME_REGRESSION]")
    return ordered
