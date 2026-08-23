from dataclasses import dataclass
from .quorum import QuorumResult
from .refusal import Refused
@dataclass(frozen=True)
class ExpectedPolicy:
    generation:int; policy_digest:str; frontier_digest:str
    def __post_init__(self):
        if self.generation<0: raise Refused("INVALID_POLICY_GENERATION")
def admit_expected(quorum:QuorumResult, expected:ExpectedPolicy)->None:
    if quorum.policy_digest is None: raise Refused("NO_REPLICA_QUORUM")
    if quorum.generation!=expected.generation: raise Refused("STALE_REPLICA_GENERATION")
    if quorum.policy_digest!=expected.policy_digest: raise Refused("POLICY_DIGEST_MISMATCH")
    if quorum.frontier_digest!=expected.frontier_digest: raise Refused("POLICY_FRONTIER_MISMATCH")
