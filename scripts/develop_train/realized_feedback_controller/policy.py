from dataclasses import dataclass
from enum import StrEnum
import re
from .errors import Refused

class BaseStrategy(StrEnum):
    MAX_INFORMATION = "MAX_INFORMATION"
    INFORMATION_PER_COST = "INFORMATION_PER_COST"
    MAX_INDEPENDENCE = "MAX_INDEPENDENCE"
    UCB_DISCOVERY = "UCB_DISCOVERY"
    MINIMAX_LATENCY = "MINIMAX_LATENCY"

class FeedbackStrategy(StrEnum):
    HOLD = "HOLD"
    BIAS_CORRECT = "BIAS_CORRECT"
    DOWNSHIFT_UNDERPERFORMER = "DOWNSHIFT_UNDERPERFORMER"
    EXPLORE_DRIFT = "EXPLORE_DRIFT"
    MINIMAX_REGRET = "MINIMAX_REGRET"

@dataclass(frozen=True)
class PolicyIdentity:
    policy_id: str
    generation: int
    digest: str
    strategy: BaseStrategy

    def __post_init__(self):
        if not self.policy_id or self.generation < 0 or not re.fullmatch(r"[0-9a-f]{64}", self.digest):
            raise Refused("REFUSED_INVALID_POLICY_IDENTITY")
