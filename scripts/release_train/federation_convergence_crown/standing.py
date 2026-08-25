from .refusal import refuse
def compute_standing(*, fixed, blockers=(), failed=False, complete=False):
    if failed:
        return "BUILD_BROKEN"
    if blockers:
        return "BLOCKED"
    if not complete:
        return "UNKNOWN"
    if fixed:
        return "PARTIAL_ALIVE"
    return "UNKNOWN"

def require_receiptable(standing):
    if standing in {"BUILD_BROKEN","BLOCKED","UNKNOWN"}:
        refuse("NON_RECEIPTABLE_STANDING",standing)
    return True
