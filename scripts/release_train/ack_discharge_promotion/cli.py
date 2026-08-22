from __future__ import annotations
import json, sys
from datetime import datetime
from .subject import Subject
from .invalidation import Invalidation
from .graph import DependencyGraph
from .witness import Witness
from .strategy import Strategy
from .engine import qualify

def main() -> int:
    data=json.load(sys.stdin)
    invalidation=Invalidation(Subject.parse(data["producer"]),data["event_id"],data["kind"],datetime.fromisoformat(data["at"]),data.get("replacement_receipt"))
    edges=tuple((Subject.parse(a),Subject.parse(b)) for a,b in data["edges"])
    graph=DependencyGraph(edges)
    witnesses=tuple(Witness(Subject.parse(w["consumer"]),data["event_id"],w["state"],datetime.fromisoformat(w["at"]),w.get("result")) for w in data.get("witnesses",[]))
    strategy_data=data["strategy"]
    strategy=Strategy(strategy_data["kind"],strategy_data.get("quorum"),tuple(Subject.parse(x) for x in strategy_data.get("critical",[])))
    result=qualify(invalidation=invalidation,graph=graph,witnesses=witnesses,strategy=strategy,
                   require_durable=data.get("require_durable",False),require_transactional=data.get("require_transactional",False))
    json.dump(result,sys.stdout,sort_keys=True,separators=(",",":"))
    sys.stdout.write("\n")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
