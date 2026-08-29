from __future__ import annotations
from dataclasses import asdict
from typing import Any
from .authority import ProposedAction, admit_actions
from .duplicates import reconcile
from .evidence import Evidence, standing
from .graph import Edge
from .ladder import Gate, evaluate
from .lineage import Predecessor, admit_predecessor
from .receipt import manufacture
from .selector import Candidate, select
from .window import ObservationWindow

LINEAGE_KEY="DMEDI_IMPLEMENT_25_COMMIT"

def manufacture_train(spec: dict[str, Any]) -> dict[str, Any]:
    window=ObservationWindow.admit(spec["since"],spec["until"])
    rows=[Evidence.admit(window=window,**row) for row in spec.get("evidence",[])]
    rows=reconcile(rows)
    edges=[Edge(**edge) for edge in spec.get("dependencies",[])]
    candidates=[Candidate(**candidate) for candidate in spec.get("candidates",[])]
    chosen, closure=select(candidates,edges)
    actions=admit_actions(ProposedAction(**action) for action in spec.get("actions",[]))
    pred=None
    if spec.get("predecessor"):
        raw=spec["predecessor"]
        from .subject import Subject
        pred=Predecessor(
            key=raw["key"],pr_url=raw["pr_url"],state=raw["state"],
            head=Subject.admit(raw["head_repo"],raw["head_sha"]),
            base_repo=raw["base_repo"],base_sha=raw["base_sha"],contained=raw.get("contained",False))
    lineage=admit_predecessor(LINEAGE_KEY,pred)
    gates=[Gate(**g) for g in spec.get("gates",[])]
    payload={
        "schema":"chatman.release-train.plan/1",
        "lineage_key":LINEAGE_KEY,
        "lineage_subject":lineage,
        "window":{"since":window.since.isoformat(),"until":window.until.isoformat()},
        "observations":[asdict(r) for r in rows],
        "observation_standing":standing(rows),
        "selected_candidate":asdict(chosen),
        "dependency_closure":list(closure),
        "actions":[asdict(a) for a in actions],
        "verification_standing":evaluate(gates),
        "gates":[asdict(g) for g in gates],
    }
    return manufacture(payload)
