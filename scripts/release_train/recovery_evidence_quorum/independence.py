RELATIONS={"SAME_EVIDENCE","CORRELATED","INDEPENDENT","UNKNOWN"}
class IndependenceEvidence:
    def __init__(self, pairs=()):
        self.pairs={frozenset((a,b)):r for a,b,r in pairs}
        if any(r not in RELATIONS for r in self.pairs.values()): raise ValueError("REFUSED[INVALID_INDEPENDENCE_RELATION]")
    def relation(self,a,b,provenance):
        if a.evidence_id==b.evidence_id:return "SAME_EVIDENCE"
        explicit=self.pairs.get(frozenset((a.evidence_id,b.evidence_id)))
        if explicit=="INDEPENDENT": return "INDEPENDENT"
        if explicit in {"CORRELATED","SAME_EVIDENCE"}: return explicit
        if provenance.derives(a.evidence_id,b.evidence_id) or provenance.derives(b.evidence_id,a.evidence_id): return "CORRELATED"
        if a.source.producer==b.source.producer or a.source.run_id==b.source.run_id or a.source.artifact_id==b.source.artifact_id or a.source.family==b.source.family:return "CORRELATED"
        return explicit or "UNKNOWN"
