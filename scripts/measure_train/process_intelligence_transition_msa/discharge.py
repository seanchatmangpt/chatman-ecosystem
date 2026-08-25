from dataclasses import dataclass
from .subject import Refused

@dataclass(frozen=True, order=True)
class Discharge:
    obligation_id: str
    before_state: str
    after_state: str
    proof_source_ids: tuple[str, ...]

def discharge(before_census, after_census, after_evidence):
    before = {row[0]: row[3] for row in before_census}
    after = {row[0]: row[3] for row in after_census}
    result = []
    for oid, after_state in sorted(after.items()):
        before_state = before.get(oid, "UNKNOWN")
        if before_state != "PASS" and after_state == "PASS":
            sources = tuple(sorted({e.source_id for e in after_evidence if e.obligation_id == oid and e.state == "PASS"}))
            if not sources:
                raise Refused("REFUSED[PASS_WITHOUT_DISCHARGE_SOURCE]")
            result.append(Discharge(oid, before_state, after_state, sources))
    return tuple(result)
