from dataclasses import dataclass
from .subject import Refused

@dataclass(frozen=True)
class ModelVersion:
    generation: int
    model: object

def resolve_frontier(versions):
    if not versions: return {"state":"UNKNOWN","current":None,"historical":()}
    max_gen=max(v.generation for v in versions)
    current=[v for v in versions if v.generation==max_gen]
    ids={v.model.model_id for v in current}
    if len(ids)!=1: raise Refused("REFUSED[DIVERGENT_CALIBRATION_FRONTIER]")
    chosen=sorted(current,key=lambda v:v.model.model_id)[0]
    historical=tuple(sorted((v for v in versions if v is not chosen),key=lambda v:(v.generation,v.model.model_id)))
    return {"state":"CURRENT","current":chosen,"historical":historical}
