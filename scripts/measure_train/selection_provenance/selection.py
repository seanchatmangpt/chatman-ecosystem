import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused
from .strategy import StrategyBinding

@dataclass(frozen=True)
class SelectionEvidence:
    consumer: Subject
    strategy: StrategyBinding
    candidate_ids: tuple[str, ...]
    selected_cut_id: str
    selector_receipt: str
    observed_at: datetime
    selector_id: str

    def __post_init__(self):
        if not self.selector_id.strip():
            raise Refused("REFUSED[EMPTY_SELECTOR_ID]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_SELECTION_TIME]")
        if len(self.selector_receipt) != 64:
            raise Refused("REFUSED[INVALID_SELECTOR_RECEIPT]")
        if len(set(self.candidate_ids)) != len(self.candidate_ids):
            raise Refused("REFUSED[DUPLICATE_CANDIDATE_ID]")
        if self.selected_cut_id not in self.candidate_ids:
            raise Refused("REFUSED[SELECTED_CUT_OUTSIDE_CANDIDATES]")

    @property
    def candidate_set_digest(self):
        raw = json.dumps(sorted(self.candidate_ids), separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()
