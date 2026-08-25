from dataclasses import dataclass
from .geometry import population_geometry
from .support import admit_support
from .weights import importance_weights
from .population import Population
from .stress import StressWorld
from .refusal import Refused

@dataclass(frozen=True)
class WorldResult:
    kind: str
    admitted: bool
    risk_ceiling: float
    ess: float
    shift: float
    refusal: str | None = None

@dataclass(frozen=True)
class InvarianceWitness:
    worlds: tuple[WorldResult,...]
    worst_risk: float
    minimum_ess: float
    maximum_shift: float
    invariant: bool


def evaluate_worlds(source: Population,target: Population,worlds: tuple[StressWorld,...],risk_ceiling: float,max_shift: float,min_ess: float,cap: float=10.0) -> InvarianceWitness:
    results=[]
    for world in worlds:
        try:
            s,t=world.populations(source,target); admit_support(s,t); g=population_geometry(s,t); w=importance_weights(s,t,cap)
            ok=g.total_variation<=max_shift and w.ess>=min_ess
            results.append(WorldResult(world.kind.value,ok,risk_ceiling,w.ess,g.total_variation,None if ok else 'BOUND_EXCEEDED'))
        except (ValueError, ZeroDivisionError) as exc:
            code=exc.code if isinstance(exc,Refused) else type(exc).__name__
            results.append(WorldResult(world.kind.value,False,1.0,0.0,1.0,code))
    worst=max((r.risk_ceiling for r in results),default=1.0)
    me=min((r.ess for r in results),default=0.0); ms=max((r.shift for r in results),default=1.0)
    return InvarianceWitness(tuple(results),worst,me,ms,bool(results) and all(r.admitted for r in results))
