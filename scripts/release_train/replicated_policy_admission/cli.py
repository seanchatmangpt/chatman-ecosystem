import json,sys
from datetime import datetime
from .subject import Subject
from .vector_clock import VectorClock
from .replica import ReplicaPolicyState
from .lease import Lease
from .policy import ExpectedPolicy
from .dependency import DependencyGraph
from .engine import qualify
def manufacture(payload:dict)->dict:
    subject=Subject(payload["repo"],payload["sha"])
    states=[ReplicaPolicyState(r["id"],subject,r["generation"],r["policy_digest"],r["frontier_digest"],VectorClock.from_dict(r["clock"])) for r in payload["replicas"]]
    lease=Lease(datetime.fromisoformat(payload["not_before"]),datetime.fromisoformat(payload["expires_at"]))
    expected=ExpectedPolicy(payload["generation"],payload["policy_digest"],payload["frontier_digest"])
    deps=DependencyGraph(tuple(tuple(x) for x in payload.get("edges",[])),tuple(tuple(x) for x in payload.get("standing",[])))
    q=qualify(subject,states,lease,datetime.fromisoformat(payload["at"]),expected,deps)
    return {"standing":q.standing,"reason":q.reason,"receipt":q.receipt.body,"digest":q.receipt.digest}
def main()->None:
    json.dump(manufacture(json.load(sys.stdin)),sys.stdout,sort_keys=True,separators=(",",":"));sys.stdout.write("\n")
if __name__=="__main__": main()
