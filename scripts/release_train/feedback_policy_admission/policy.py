from dataclasses import dataclass
from enum import Enum
import re
from .errors import Refused
class FeedbackStrategy(str, Enum):
    HOLD="HOLD"
    BIAS_CORRECT="BIAS_CORRECT"
    DOWNSHIFT_UNDERPERFORMER="DOWNSHIFT_UNDERPERFORMER"
    EXPLORE_DRIFT="EXPLORE_DRIFT"
    MINIMAX_REGRET="MINIMAX_REGRET"
_DIGEST=re.compile(r"^[0-9a-f]{64}$")
@dataclass(frozen=True)
class PolicyIdentity:
    policy_id: str
    generation: int
    digest: str
    strategy: FeedbackStrategy
    def __post_init__(self):
        if not self.policy_id or self.generation < 0 or not _DIGEST.fullmatch(self.digest):
            raise Refused("INVALID_POLICY_IDENTITY")
