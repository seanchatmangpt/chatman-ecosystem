from __future__ import annotations

import json, sys
from datetime import datetime
from .engine import manufacture_plan
from .evidence import Evidence
from .obligation import Obligation
from .subject import Subject
from .supersession import Supersession

def main() -> int:
    raw=json.load(sys.stdin)
    evidence_by_repo={}
    for repo, rows in raw["evidence"].items():
        evidence_by_repo[repo]=[Evidence(r["id"], Subject.parse(r["subject"]), r["scope"], r["outcome"], datetime.fromisoformat(r["observed_at"].replace("Z","+00:00")), r.get("run_id"), r.get("artifact_id")) for r in rows]
    relations={repo:[Supersession(**r) for r in rows] for repo,rows in raw.get("supersession",{}).items()}
    obligations=tuple(Obligation(**o) for o in raw["obligations"])
    result=manufacture_plan(predecessor=raw["predecessor"], evidence_by_repo=evidence_by_repo, relations_by_repo=relations, obligations=obligations, graph={k:tuple(v) for k,v in raw["graph"].items()})
    json.dump(result, sys.stdout, sort_keys=True, separators=(",",":")); sys.stdout.write("\n")
    return 0

if __name__ == "__main__": raise SystemExit(main())
