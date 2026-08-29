from dataclasses import dataclass
@dataclass(frozen=True)
class IndependenceProof:
    a: str; b: str; independent: bool
    def normalized(self): return tuple(sorted((self.a,self.b)))

def relation(a,b,proofs=()):
    if a.fingerprint==b.fingerprint: return "SAME_EVIDENCE"
    proof={p.normalized():p.independent for p in proofs}.get(tuple(sorted((a.fingerprint,b.fingerprint))))
    if proof is True: return "INDEPENDENT"
    if a.family==b.family or a.producer==b.producer or a.run_id==b.run_id or a.artifact_id==b.artifact_id: return "CORRELATED"
    return "UNKNOWN"

def independent_clusters(sources, proofs=()):
    groups=[]
    for s in sources:
        placed=False
        for g in groups:
            if any(relation(s,x,proofs) in {"SAME_EVIDENCE","CORRELATED"} for x in g):
                g.append(s); placed=True; break
        if not placed: groups.append([s])
    return groups
