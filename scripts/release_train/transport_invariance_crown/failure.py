from .refusal import require

REQUIRED_FAILURES=frozenset({'node','partition','latency','loss','version','certificate','ambiguous_do'})

def admit_failure_worlds(worlds: dict[str,bool]) -> tuple[str,...]:
    missing=REQUIRED_FAILURES-set(worlds)
    require(not missing,"INCOMPLETE_FAILURE_TOPOLOGY",','.join(sorted(missing)))
    failed=[k for k in REQUIRED_FAILURES if not worlds[k]]
    require(not failed,"FAILURE_WORLD_UNQUALIFIED",','.join(sorted(failed)))
    return tuple(sorted(REQUIRED_FAILURES))
