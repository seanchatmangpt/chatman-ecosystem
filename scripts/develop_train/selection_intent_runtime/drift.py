from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .intent import SelectionIntent
from .policy import StrategyPolicy
from .frontier import CandidateFrontier
class DriftKind(str,Enum):
    EXACT="EXACT"; POLICY="POLICY"; FRONTIER="FRONTIER"; POLICY_AND_FRONTIER="POLICY_AND_FRONTIER"; LEASE_EXPIRED="LEASE_EXPIRED"
@dataclass(frozen=True,slots=True)
class Drift:
    kind:DriftKind; policy_changed:bool; frontier_changed:bool
def classify(intent:SelectionIntent,policy:StrategyPolicy,frontier:CandidateFrontier,now)->Drift:
    p=intent.policy_digest!=policy.digest; f=intent.frontier_digest!=frontier.digest
    if not intent.lease.active(now): return Drift(DriftKind.LEASE_EXPIRED,p,f)
    return Drift(DriftKind.POLICY_AND_FRONTIER if p and f else DriftKind.POLICY if p else DriftKind.FRONTIER if f else DriftKind.EXACT,p,f)
