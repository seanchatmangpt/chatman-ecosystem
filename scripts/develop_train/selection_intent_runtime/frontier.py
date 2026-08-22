from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib, json
from .identity import Subject
@dataclass(frozen=True, slots=True)
class CutCandidate:
    cut_id:str; generation:int; producer_generations:tuple[tuple[Subject,int],...]; observed_at:datetime
    def __post_init__(self)->None:
        if not self.cut_id or self.generation<0: raise ValueError("REFUSED[INVALID_CUT]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None: raise ValueError("REFUSED[NAIVE_CUT_TIME]")
        repos=[s.repository for s,_ in self.producer_generations]
        if len(repos)!=len(set(repos)) or any(g<0 for _,g in self.producer_generations): raise ValueError("REFUSED[INVALID_PRODUCER_FRONTIER]")
    @property
    def freshness(self)->int: return sum(g for _,g in self.producer_generations)
    @property
    def skew(self)->int:
        gs=[g for _,g in self.producer_generations]; return max(gs)-min(gs) if gs else 0
@dataclass(frozen=True, slots=True)
class CandidateFrontier:
    candidates:tuple[CutCandidate,...]
    def __post_init__(self)->None:
        ids=[c.cut_id for c in self.candidates]
        if not ids or len(ids)!=len(set(ids)): raise ValueError("REFUSED[INVALID_CANDIDATE_FRONTIER]")
    @property
    def digest(self)->str:
        rows=[]
        for c in sorted(self.candidates,key=lambda x:x.cut_id):
            rows.append({"cut_id":c.cut_id,"generation":c.generation,"producer_generations":sorted((s.coordinate,g) for s,g in c.producer_generations),"observed_at":c.observed_at.astimezone(timezone.utc).isoformat()})
        return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(",",":")).encode()).hexdigest()
