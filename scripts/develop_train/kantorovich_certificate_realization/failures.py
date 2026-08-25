from enum import Enum
from .errors import Refused

class World(str, Enum):
    NODE_DOWN = "NODE_DOWN"
    PARTITION = "PARTITION"
    LATENCY = "LATENCY"
    LOSS = "LOSS"
    VERSION_SKEW = "VERSION_SKEW"
    CERTIFICATE = "CERTIFICATE"
    AMBIGUOUS_DO = "AMBIGUOUS_DO"

REQUIRED = frozenset(World)


def require_complete(worlds):
    seen = {World(world) for world in worlds}
    missing = REQUIRED - seen
    if missing:
        raise Refused("INCOMPLETE_CERTIFICATE_FAILURE_TOPOLOGY", ",".join(sorted(world.value for world in missing)))
    return frozenset(seen)
