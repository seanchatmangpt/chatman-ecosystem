from .subject import Refused

def admit_recovery(proof, current_before, current_after, current_witnesses, now):
    if not proof.lease.active(now): raise Refused("REFUSED[INACTIVE_RECOVERY_PROOF_LEASE]")
    if proof.strategy=="RESELECT":
        return "ADMITTED_RESELECT"
    w=proof.witness
    if w.before != current_before: raise Refused("REFUSED[STALE_WITNESS_BEFORE_CONTEXT]")
    if w.after != current_after: raise Refused("REFUSED[STALE_WITNESS_AFTER_CONTEXT]")
    if w not in current_witnesses: raise Refused("REFUSED[SUPERSEDED_COMPATIBILITY_WITNESS]")
    if w.result!="PASS":
        raise Refused("REFUSED[NONPASS_COMPATIBILITY_WITNESS]")
    if proof.strategy=="REBIND_EQUIVALENT" and w.kind not in {"EXACT","SEMANTIC_EQUIVALENT"}:
        raise Refused("REFUSED[INSUFFICIENT_EQUIVALENCE_WITNESS]")
    if proof.strategy=="REQUALIFY_COMPATIBLE" and w.kind not in {"EXACT","SEMANTIC_EQUIVALENT","BACKWARD_COMPATIBLE"}:
        raise Refused("REFUSED[INSUFFICIENT_COMPATIBILITY_WITNESS]")
    return "ADMITTED"
