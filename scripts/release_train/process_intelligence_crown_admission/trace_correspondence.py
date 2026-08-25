from dataclasses import dataclass
from .refusal import require

@dataclass(frozen=True)
class TraceWitness:
    rail: str
    traces: tuple[tuple[str, ...], ...]
    semantic_digest: str

def compare_trace_sets(reference, witness: TraceWitness):
    ref=frozenset(reference); got=frozenset(witness.traces)
    missing=tuple(sorted(ref-got)); extra=tuple(sorted(got-ref))
    return missing, extra

def require_complete(reference, witness: TraceWitness) -> None:
    missing,extra=compare_trace_sets(reference,witness)
    require(not missing, "POWL_INCOMPLETE_TRACE_CORRESPONDENCE", repr(missing))
    require(not extra, "POWL_UNSOUND_TRACE_CORRESPONDENCE", repr(extra))
