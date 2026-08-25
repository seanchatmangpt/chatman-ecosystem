from dataclasses import dataclass
from .reactor_projection import Projection, require_correspondence
from .trace_correspondence import TraceWitness, require_complete
from .refusal import require

@dataclass(frozen=True)
class DifferentialWitness:
    left: Projection
    right: Projection
    left_traces: TraceWitness
    right_traces: TraceWitness

def require_equivalent(reference_traces, witness: DifferentialWitness) -> None:
    require_correspondence(witness.left, witness.right)
    require(witness.left_traces.semantic_digest == witness.left.semantic_digest, "LEFT_TRACE_DIGEST_DRIFT")
    require(witness.right_traces.semantic_digest == witness.right.semantic_digest, "RIGHT_TRACE_DIGEST_DRIFT")
    require_complete(reference_traces, witness.left_traces)
    require_complete(reference_traces, witness.right_traces)
