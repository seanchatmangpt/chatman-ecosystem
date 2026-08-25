from dataclasses import dataclass
from .refusal import refuse
@dataclass(frozen=True)
class Calibration: generation:int; digest:str; support:int; error_ppm:int
def current_frontier(items):
    items=list(items)
    if not items: refuse("MISSING_CALIBRATION")
    g=max(i.generation for i in items); cur=[i for i in items if i.generation==g]
    if len({i.digest for i in cur})!=1: refuse("DIVERGENT_CURRENT_CALIBRATION")
    if any(i.support<=0 or i.error_ppm<0 for i in cur): refuse("INVALID_CALIBRATION")
    return cur[0]
