from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True)
class Stratum:
    methodology: str
    engine: str
    region: str
    root: str
    risk: float
    support: int

def worst(values, minimum_support=1):
    values = tuple(values)
    if not values:
        raise Refused("NO_STRATA")
    if any(item.support < minimum_support for item in values):
        raise Refused("WEAK_STRATUM_SUPPORT")
    return max(values, key=lambda item: (item.risk, item.methodology, item.engine, item.region, item.root))
