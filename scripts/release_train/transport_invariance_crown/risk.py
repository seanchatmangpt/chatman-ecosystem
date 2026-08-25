from dataclasses import dataclass
from .refusal import require

@dataclass(frozen=True)
class Observation:
    cell: str
    loss: float
    propensity: float

    def __post_init__(self) -> None:
        require(0 <= self.loss <= 1, "INVALID_LOSS")
        require(0 < self.propensity <= 1, "INVALID_PROPENSITY")

@dataclass(frozen=True)
class RiskEnvelope:
    ht: float
    self_normalized: float
    direct: float
    disagreement: float
    lower: float
    upper: float


def estimate_risk(observations: tuple[Observation,...], weights: dict[str,float]) -> RiskEnvelope:
    require(bool(observations), "NO_OUTCOME_SUPPORT")
    terms=[(weights.get(o.cell,0.0)/o.propensity,o.loss) for o in observations]
    require(any(w>0 for w,_ in terms), "NO_WEIGHTED_SUPPORT")
    ht=sum(w*l for w,l in terms)/len(observations)
    den=sum(w for w,_ in terms)
    sn=sum(w*l for w,l in terms)/den
    direct=sum(l for _,l in terms)/len(terms)
    lo=min(ht,sn,direct); hi=max(ht,sn,direct)
    return RiskEnvelope(ht,sn,direct,hi-lo,lo,hi)
