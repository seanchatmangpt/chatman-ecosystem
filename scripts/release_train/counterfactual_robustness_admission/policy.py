from dataclasses import dataclass
from enum import Enum
from .refusal import refuse

class RobustStrategy(str,Enum):
    MAX_LOWER="MAX_LOWER"
    MIN_WIDTH="MIN_WIDTH"
    MAX_BREAKDOWN="MAX_BREAKDOWN"
    HOLD="HOLD"

@dataclass(frozen=True)
class PolicyIdentity:
    policy_id: str
    generation: int
    digest: str
    def __post_init__(self):
        if not self.policy_id or self.generation < 0 or len(self.digest)!=64 or any(c not in '0123456789abcdef' for c in self.digest):
            refuse("INVALID_POLICY_IDENTITY")
