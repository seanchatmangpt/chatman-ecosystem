from dataclasses import dataclass
@dataclass(frozen=True)
class Qualification:
    standing:str; blockers:frozenset; evidence_digest:str
def compute(*,blockers=(),certificate=True,calibrated=True,global_ok=True):
    b=frozenset(blockers)
    if any(str(x).startswith("BUILD_BROKEN") for x in b): return Qualification("BUILD_BROKEN",b,"")
    if b: return Qualification("BLOCKED",b,"")
    if not certificate or not calibrated or not global_ok: return Qualification("UNSUPPORTED",b,"")
    return Qualification("PARTIAL_ALIVE",b,"qualified")
