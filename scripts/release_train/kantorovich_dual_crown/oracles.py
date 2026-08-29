from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class SemanticOracle:
    kind:str; implementation:str; model:str; digest:str
def require_oracles(xs):
    kinds={x.kind for x in xs}
    if not {"POWL","OCEL"}<=kinds: raise Refused("ORACLE_KIND_GAP")
    chosen=[next(x for x in xs if x.kind==k) for k in ("POWL","OCEL")]
    if len({x.implementation for x in chosen})<2 or len({x.model for x in chosen})<2: raise Refused("ORACLE_NOT_INDEPENDENT")
    return True
