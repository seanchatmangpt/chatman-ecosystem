from dataclasses import dataclass
@dataclass(frozen=True, order=True)
class IndependenceProof:
    left:str
    right:str
    proof_id:str
def independent_pairs(sensors, proofs):
    proofset={tuple(sorted((p.left,p.right))) for p in proofs}
    out=set()
    for i,a in enumerate(sensors):
        for b in sensors[i+1:]:
            if a.family!=b.family and a.domain!=b.domain and tuple(sorted((a.sensor_id,b.sensor_id))) in proofset:
                out.add(tuple(sorted((a.sensor_id,b.sensor_id))))
    return out
