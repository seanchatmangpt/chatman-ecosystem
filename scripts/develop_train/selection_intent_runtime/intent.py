from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .identity import Subject
@dataclass(frozen=True, slots=True)
class IntentLease:
    not_before:datetime; expires_at:datetime
    def __post_init__(self)->None:
        if any(t.tzinfo is None or t.utcoffset() is None for t in (self.not_before,self.expires_at)): raise ValueError("REFUSED[NAIVE_INTENT_LEASE]")
        if self.expires_at<=self.not_before: raise ValueError("REFUSED[INVALID_INTENT_LEASE]")
    def active(self,now:datetime)->bool:
        if now.tzinfo is None or now.utcoffset() is None: raise ValueError("REFUSED[NAIVE_NOW]")
        return self.not_before<=now<self.expires_at
@dataclass(frozen=True, slots=True)
class SelectionIntent:
    consumer:Subject; selected_cut_id:str; policy_digest:str; frontier_digest:str; nonce:str; lease:IntentLease
    def __post_init__(self)->None:
        if not self.selected_cut_id or len(self.policy_digest)!=64 or len(self.frontier_digest)!=64: raise ValueError("REFUSED[INVALID_SELECTION_INTENT]")
        if not self.nonce: raise ValueError("REFUSED[EMPTY_INTENT_NONCE]")
