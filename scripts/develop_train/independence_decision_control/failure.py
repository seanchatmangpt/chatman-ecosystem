from .errors import Refused

REQUIRED_FAILURES = frozenset({"node", "partition", "latency", "loss", "version", "certificate", "ambiguous-do"})


def require_failures(values):
    if not REQUIRED_FAILURES.issubset(set(values)):
        raise Refused("INCOMPLETE_FAILURE_TOPOLOGY")
    return True
