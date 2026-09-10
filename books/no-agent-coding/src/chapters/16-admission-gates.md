# 16. Public Ontology and Admission Gates

**Executive thesis:** A deterministic factory needs a narrow, explicit admissible input space; otherwise the generator merely accelerates ambiguity.

## Constraints are not bureaucracy

Admission gates are the executable version of architectural intent. They can refuse missing identity, unsupported ontology, conflicting authority, malformed topology, stale evidence, unsafe composition, or a projection without an owner. The point is not to make every domain fully formal; it is to make the manufacturing boundary explicit.

## Multiple courts are legitimate

Different claims need different admission mechanisms. Structural graph constraints may use SHACL. Query-level predicates may use SPARQL ASK. Mathematical claims may use a proof assistant. Runtime claims need real execution. Commercial or organizational claims may need external provider evidence. One verifier should not silently claim authority outside its court.

## Typed refusal preserves truth

A system that cannot satisfy the gate should return a meaningful refusal rather than degrade to a weaker unreported behavior. REFUSED, BLOCKED, UNKNOWN, and UNSUPPORTED are information. They preserve the edge of the admitted world and prevent false done.

## Operating practice

Write the negative fixture before celebrating the positive path. For every admission rule, name at least one malformed or unauthorized case that must fail. If a gate cannot distinguish the falsifier, it is not yet a useful gate.

## Diagnostic question

What malformed or unauthorized input must your admission gate refuse?
