from dataclasses import dataclass
from .independence import independent_clique

@dataclass(frozen=True)
class Consensus:
    verdict: str
    admitted_detectors: tuple
    drift_votes: int
    stable_votes: int

def decide(admitted_votes, proofs, quorum=2):
    if quorum < 2: raise ValueError("REFUSED[WEAK_QUORUM]")
    by={a.vote.detector.fingerprint:a for a in admitted_votes}; clique=independent_clique(by,proofs); chosen=[by[n] for n in clique]
    drift=sum(a.vote.verdict=="DRIFT" for a in chosen); stable=sum(a.vote.verdict=="STABLE" for a in chosen); fail=any(a.vote.verdict=="FAIL" for a in chosen)
    verdict="FAIL" if fail else ("DRIFT_CONFIRMED" if drift>=quorum else ("STABLE_CONFIRMED" if stable>=quorum else "INSUFFICIENT"))
    return Consensus(verdict,tuple(clique),drift,stable)
