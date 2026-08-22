from .admission import admit_witness
from .likelihood import contribution
from .sequential import decide
from .independence import independent_clusters, relation
from .standing import bounded_standing
from .persistence import select_store
from .authority import require_action
from .receipt import Receipt

def qualify(subject, attempt_id, sources, witnesses, models, proofs, graph, standings, need, now, min_trials=6, required_clusters=2):
    require_action("SELECT")
    byfp={s.fingerprint:s for s in sources}; bymodel={m.source_id:m for m in models}
    admissions=[]; contribs=[]
    for w in witnesses:
        s=byfp[w.source_fingerprint]; m=bymodel[w.source_fingerprint]
        a=admit_witness(w,s,m,now,min_trials); admissions.append(a)
        contribs.append(contribution(m,w.outcome) if a["admitted"] else contribution(m,"UNKNOWN"))
    clusters=independent_clusters(sources,proofs)
    independent=0
    for i,g in enumerate(clusters):
        if i==0: independent=1; continue
        if all(relation(g[0],h[0],proofs)=="INDEPENDENT" for h in clusters[:i]): independent+=1
    decision=decide(contribs)
    blockers=graph.blockers(subject.exact,standings)
    standing=bounded_standing(witnesses,admissions,decision,independent,required_clusters,blockers)
    store=select_store(need)
    require_action("CONSTRUCT")
    payload={"subject":subject.exact,"attempt_id":attempt_id,"standing":standing,"independent_clusters":independent,"decision":decision.decision,"statistic":decision.statistic,"blockers":blockers,"store":store,"phases":["VERIFY","CONSTRUCT"]}
    r=Receipt.manufacture(payload)
    return {**payload,"receipt":r,"replay":r.replay()}
