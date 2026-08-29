from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class OracleWitness:
    kind:str; implementation_digest:str; model_digest:str; evidence_root:str
def require_oracles(witnesses):
    w=tuple(witnesses)
    if not {"POWL","OCEL"}<={x.kind for x in w}: raise Refused("MISSING_REFERENCE_ORACLE")
    for kind in ("POWL","OCEL"):
        ks=[x for x in w if x.kind==kind]
        if len(ks)<2 or len({x.implementation_digest for x in ks})<2 or len({x.model_digest for x in ks})<2 or len({x.evidence_root for x in ks})<2: raise Refused(f"NONINDEPENDENT_{kind}_ORACLE")
    return True
