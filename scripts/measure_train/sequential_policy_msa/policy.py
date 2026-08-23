import re
from dataclasses import dataclass
from .refusal import Refused

STRATEGIES={"MAX_INFORMATION","INFORMATION_PER_COST","MAX_INDEPENDENCE","UCB_DISCOVERY","MINIMAX_LATENCY"}

@dataclass(frozen=True, order=True)
class PolicyIdentity:
    policy_id: str
    generation: int
    digest: str
    strategy: str

    def __post_init__(self):
        if not self.policy_id.strip():
            raise Refused("REFUSED[EMPTY_POLICY_ID]")
        if self.generation < 0:
            raise Refused("REFUSED[INVALID_POLICY_GENERATION]")
        if not re.fullmatch(r"[0-9a-f]{64}", self.digest):
            raise Refused("REFUSED[INVALID_POLICY_DIGEST]")
        if self.strategy not in STRATEGIES:
            raise Refused("REFUSED[UNKNOWN_POLICY_STRATEGY]")
