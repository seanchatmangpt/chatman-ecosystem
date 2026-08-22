from .frontier import current_witnesses
from .clusters import correlated_clusters
from .diversity import effective_source_diversity
from .policy import standing_for
from .receipt import manufacture_receipt,replay
from .authority import require_action
def qualify(subject,attempt_id,witnesses,now,independence,provenance,policy,dependency_graph,dependency_standing,store="MEMORY"):
    require_action("CONSTRUCT")
    if store not in {"MEMORY","JSONL","SQLITE"}: raise ValueError("REFUSED[UNKNOWN_STORE]")
    current,historical=current_witnesses(witnesses,attempt_id,now)
    clusters=correlated_clusters(current,independence,provenance)
    blockers=dependency_graph.blockers(dependency_standing)
    standing=standing_for(clusters,policy,blockers)
    numerator,denominator=effective_source_diversity(clusters)
    payload={"subject":subject.key,"attempt_id":attempt_id,"cluster_count":len(clusters),"diversity":[numerator,denominator],"blockers":list(blockers),"standing":standing,"store":store,"phases":["VERIFY","CONSTRUCT"]}
    receipt=manufacture_receipt(payload)
    return {"standing":standing,"clusters":clusters,"historical":historical,"receipt":receipt,"replay":replay(receipt)}
