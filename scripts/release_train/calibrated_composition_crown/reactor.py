from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class ReactorCorrespondence:
    semantic_digest:str; projection_digest:str; trace_digest:str; receipt_subject_digest:str
def require_correspondence(c, expected_semantic, expected_trace):
    if c.semantic_digest!=expected_semantic or c.receipt_subject_digest!=expected_semantic: raise Refused("REACTOR_SUBJECT_DRIFT")
    if c.trace_digest!=expected_trace: raise Refused("REACTOR_TRACE_DRIFT")
    if len(c.projection_digest)!=64: raise Refused("INVALID_PROJECTION_DIGEST")
    return True
