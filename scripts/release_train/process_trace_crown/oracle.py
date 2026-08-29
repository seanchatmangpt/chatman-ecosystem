from __future__ import annotations
from dataclasses import dataclass
from .refusal import Refused
from .trace import Trace

@dataclass(frozen=True)
class OracleWitness:
    oracle: str
    implementation_digest: str
    trace: Trace

def require_independent(witnesses: tuple[OracleWitness, ...], minimum: int = 2) -> None:
    if len(witnesses) < minimum:
        raise Refused("INSUFFICIENT_ORACLE_WITNESSES")
    digests = {w.implementation_digest for w in witnesses}
    if len(digests) < minimum:
        raise Refused("ORACLE_IMPLEMENTATION_COLLUSION")
    subjects = {w.trace.subject for w in witnesses}
    if len(subjects) != 1:
        raise Refused("ORACLE_SUBJECT_DRIFT")
