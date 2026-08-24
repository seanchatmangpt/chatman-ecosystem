from dataclasses import dataclass
from datetime import datetime, timezone
from .errors import Refused
@dataclass(frozen=True)
class ConvergenceObservation:
    observation_id: str
    generation: int
    semantic_digest: str
    controller_claim_fixed: bool
    realized_blockers: int
    realized_errors: int
    realized_churn: int
    methodology: str
    engine: str
    region: str
    evidence_root: str
    observed_at: datetime
    def __post_init__(self):
        if not self.observation_id or self.generation < 0: raise Refused("INVALID_OBSERVATION_IDENTITY")
        if len(self.semantic_digest) != 64: raise Refused("INVALID_SEMANTIC_DIGEST")
        if min(self.realized_blockers,self.realized_errors,self.realized_churn) < 0: raise Refused("NEGATIVE_REALIZATION_STATE")
        if self.observed_at.tzinfo is None: raise Refused("NAIVE_OBSERVATION_TIME")
        if any(not x for x in (self.methodology,self.engine,self.region,self.evidence_root)): raise Refused("INCOMPLETE_REALIZATION_PROVENANCE")
def admit(observations):
    obs=tuple(observations)
    if not obs: raise Refused("EMPTY_CONVERGENCE_TRAJECTORY")
    ids=[o.observation_id for o in obs]
    if len(ids)!=len(set(ids)): raise Refused("DUPLICATE_OBSERVATION")
    if any(o.observed_at > datetime.now(timezone.utc) for o in obs): raise Refused("FUTURE_OBSERVATION")
    return tuple(sorted(obs,key=lambda o:(o.generation,o.observed_at,o.observation_id)))
