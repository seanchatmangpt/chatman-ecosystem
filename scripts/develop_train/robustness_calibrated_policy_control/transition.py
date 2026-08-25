from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class PortfolioTransition:
    from_generation:int
    to_generation:int
    selected_keys:tuple[str,...]
    def __post_init__(self):
        if self.to_generation!=self.from_generation+1: raise Refused('NON_MONOTONE_GENERATION')
        if not self.selected_keys: raise Refused('EMPTY_TRANSITION')
