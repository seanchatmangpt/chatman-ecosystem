from dataclasses import dataclass
from .refusal import require

@dataclass(frozen=True, order=True)
class Stratum:
    methodology: str
    engine: str
    region: str
    evidence_root: str
    support: int
    worst_risk: float
    invariant: bool


def worst_stratum(strata: tuple[Stratum,...], min_support: int, max_risk: float) -> Stratum:
    require(bool(strata), "NO_STRATA")
    for s in strata:
        require(s.support>=min_support, "STRATUM_SUPPORT_INSUFFICIENT", f"{s.methodology}:{s.engine}:{s.region}")
    worst=max(strata,key=lambda s:(not s.invariant,s.worst_risk,-s.support,s.methodology,s.engine,s.region,s.evidence_root))
    require(worst.invariant and worst.worst_risk<=max_risk, "WORST_STRATUM_UNSAFE", worst.methodology)
    return worst
