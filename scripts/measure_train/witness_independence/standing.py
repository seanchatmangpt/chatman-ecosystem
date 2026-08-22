from dataclasses import dataclass
from .subject import Refused

@dataclass(frozen=True)
class IndependencePolicy:
    min_independent_clusters: int = 2
    required_scope: str = "REPOSITORY"
    def __post_init__(self):
        if self.min_independent_clusters < 1:
            raise Refused("REFUSED[INVALID_INDEPENDENCE_THRESHOLD]")

def evaluate(census_rows, policy):
    relevant=[r for r in census_rows if policy.required_scope in r["scopes"]]
    if not relevant:
        return "UNKNOWN"
    states={r["state"] for r in relevant}
    if "FAIL" in states:
        return "BUILD_BROKEN"
    if "CONTRADICTED" in states or "UNKNOWN" in states:
        return "UNKNOWN"
    if states=={"UNSUPPORTED"}:
        return "UNSUPPORTED"
    passing=sum(r["state"]=="PASS" for r in relevant)
    if passing < policy.min_independent_clusters:
        return "UNKNOWN"
    return "PARTIAL_ALIVE"
