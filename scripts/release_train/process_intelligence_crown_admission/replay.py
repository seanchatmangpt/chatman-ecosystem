from .receipt_dag import require_dag
from .refusal import require

def replay(nodes, expected_root: str):
    digests=require_dag(nodes)
    require(expected_root in digests, "REPLAY_ROOT_MISSING")
    by={n.digest:n for n in nodes}
    root=by[expected_root]
    require(not root.actuation_performed, "REPLAY_REPORTED_ACTUATION")
    return "REPLAY_MATCH"
