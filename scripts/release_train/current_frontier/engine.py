from __future__ import annotations

from .admission import admit_subject
from .authority import require
from .candidate import Candidate, select
from .dependency import dependency_order, propagate
from .frontier import resolve_frontier
from .obligation import Obligation
from .receipt import manufacture

def manufacture_plan(*, predecessor: str, evidence_by_repo: dict, relations_by_repo: dict, obligations: tuple[Obligation,...], graph: dict[str,tuple[str,...]]) -> dict:
    repos=set(evidence_by_repo)
    order=dependency_order(graph,repos)
    admissions=[]; standings={}
    for repo in order:
        frontier=resolve_frontier(tuple(evidence_by_repo[repo]), tuple(relations_by_repo.get(repo,())))
        adm=admit_subject(frontier.current[0].subject.canonical() if frontier.current else repo, frontier, obligations)
        admissions.append(adm); standings[repo]=adm.standing
    propagated=propagate(standings, graph, order)
    normalized=[]
    for adm in admissions:
        repo=adm.subject.split("@",1)[0]
        if propagated.get(repo) in {"BLOCKED","BUILD_BROKEN"} and adm.promotable:
            normalized.append(type(adm)(adm.subject, propagated[repo], adm.obligation_states, False, (f"dependency:{propagated[repo]}",)))
        else: normalized.append(adm)
    chosen=select((Candidate("current-frontier", tuple(normalized), len(order), 10, 1),))
    require("CONSTRUCT")
    plan={"predecessor":predecessor,"candidate":chosen.name,"subjects":[a.subject for a in chosen.admissions],"order":list(order),"phases":["VERIFY","CONSTRUCT"],"standing":"PARTIAL_ALIVE"}
    receipt=manufacture(plan)
    return {"plan":plan,"receipt":{"schema":receipt.schema,"body":receipt.body,"digest":receipt.digest}}
