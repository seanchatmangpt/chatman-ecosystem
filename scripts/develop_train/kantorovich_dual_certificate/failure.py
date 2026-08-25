from enum import Enum
from .errors import Refused
class World(str, Enum):
    NODE_DOWN="NODE_DOWN"; PARTITION="PARTITION"; LATENCY="LATENCY"; LOSS="LOSS"; VERSION_SKEW="VERSION_SKEW"; CERTIFICATE="CERTIFICATE"; AMBIGUOUS_DO="AMBIGUOUS_DO"
def require_failures(worlds):
    seen = {World(world) for world in worlds}; missing = set(World) - seen
    if missing:
        raise Refused("INCOMPLETE_FAILURE_TOPOLOGY", ",".join(sorted(world.value for world in missing)))
    return frozenset(seen)
