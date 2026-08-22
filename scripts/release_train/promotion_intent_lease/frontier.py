from dataclasses import dataclass
from .cut import CutIdentity
from .strategy import StrategyBinding

@dataclass(frozen=True)
class PromotionFrontier:
    cut: CutIdentity
    strategy: StrategyBinding
    policy_digest: str

    @property
    def strategy_digest(self) -> str:
        return self.strategy.fingerprint()
