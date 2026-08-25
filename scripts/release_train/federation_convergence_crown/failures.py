from .refusal import refuse
REQUIRED=frozenset("NODE PARTITION LATENCY LOSS VERSION CERTIFICATE AMBIGUOUS_DO".split())
def require_failures(worlds):
    missing=REQUIRED-set(worlds)
    if missing:
        refuse("INCOMPLETE_FAILURE_WORLD", ",".join(sorted(missing)))
    return True
