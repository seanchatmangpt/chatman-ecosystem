ALLOWED_STANDING={"PARTIAL_ALIVE","ALIVE"}
class PolicyRefusal(ValueError): pass
def admit_candidate(candidate, ancestry_proven: bool, source_allowed: bool, advisory_clear: bool):
    if candidate.evidence_state not in ALLOWED_STANDING: raise PolicyRefusal("REFUSED[INSUFFICIENT_EVIDENCE]")
    if not ancestry_proven: raise PolicyRefusal("REFUSED[UNPROVEN_ANCESTRY]")
    if not source_allowed: raise PolicyRefusal("REFUSED[UNADMITTED_SOURCE]")
    if not advisory_clear: raise PolicyRefusal("REFUSED[ACTIVE_ADVISORY]")
    return candidate
