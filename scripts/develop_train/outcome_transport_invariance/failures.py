from enum import Enum
from .errors import Refused

class World(str, Enum):
    NODE = "NODE"
    PARTITION = "PARTITION"
    LATENCY = "LATENCY"
    LOSS = "LOSS"
    VERSION = "VERSION"
    CERTIFICATE = "CERTIFICATE"
    AMBIGUOUS_DO = "AMBIGUOUS_DO"

REQUIRED = frozenset(World)

def require(values):
    seen = frozenset(World(value) for value in values)
    if REQUIRED - seen:
        raise Refused("INCOMPLETE_FAILURE_TOPOLOGY")
    return seen
