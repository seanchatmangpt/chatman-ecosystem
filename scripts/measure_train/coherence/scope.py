from enum import Enum
from .subject import Refusal

class ScopeRelation(str, Enum): EXACT="EXACT"; NARROWER="NARROWER"; BROADER="BROADER"; DISJOINT="DISJOINT"

def _parts(scope: str):
    if not scope or scope.startswith('/') or scope.endswith('/'): raise Refusal("INVALID_SCOPE")
    return tuple(p for p in scope.split('/') if p)

def relation(witness_scope: str, obligation_scope: str) -> ScopeRelation:
    w,o=_parts(witness_scope),_parts(obligation_scope)
    if w==o: return ScopeRelation.EXACT
    if len(w)>len(o) and w[:len(o)]==o: return ScopeRelation.NARROWER
    if len(o)>len(w) and o[:len(w)]==w: return ScopeRelation.BROADER
    return ScopeRelation.DISJOINT

def satisfies_scope(witness_scope: str, obligation_scope: str) -> bool:
    return relation(witness_scope, obligation_scope) in {ScopeRelation.EXACT, ScopeRelation.BROADER}
