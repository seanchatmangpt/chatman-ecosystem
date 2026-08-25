from .refusal import Refused
def same_semantics(a,b):
    if a.subject != b.subject: raise Refused("REFUSED[FOREIGN_SUBJECT_COMPARISON]")
    return a.semantic_digest==b.semantic_digest and a.result_digest==b.result_digest
def require_equivalent(a,b):
    if not same_semantics(a,b): raise Refused("REFUSED[PROJECTION_DIVERGENCE]")
    return True
