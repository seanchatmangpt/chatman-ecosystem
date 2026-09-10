from dataclasses import dataclass
from .strategy import StrategyBinding
from .subject import Refused

@dataclass(frozen=True)
class SelectionFrontier:
    strategy: StrategyBinding
    current_candidate_ids: tuple[str, ...]
    current_selected_cut_id: str

    def __post_init__(self):
        if len(set(self.current_candidate_ids)) != len(self.current_candidate_ids):
            raise Refused("REFUSED[DUPLICATE_FRONTIER_CANDIDATE]")
        if self.current_selected_cut_id not in self.current_candidate_ids:
            raise Refused("REFUSED[FRONTIER_SELECTION_OUTSIDE_CANDIDATES]")
