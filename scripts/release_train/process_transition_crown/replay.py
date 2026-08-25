from .receipt import Receipt
from .refusal import Refused


def replay(receipts: tuple[Receipt,...], expected_root: str) -> str:
    by_digest={r.digest():r for r in receipts}
    if expected_root not in by_digest:
        raise Refused("REPLAY_ROOT_MISSING")
    visiting=set(); seen=set()
    def visit(d):
        if d in visiting: raise Refused("RECEIPT_DAG_CYCLE")
        if d in seen:return
        r=by_digest.get(d)
        if r is None: raise Refused("RECEIPT_PARENT_MISSING",d)
        visiting.add(d)
        for p in r.parents: visit(p)
        visiting.remove(d);seen.add(d)
    visit(expected_root)
    return expected_root
