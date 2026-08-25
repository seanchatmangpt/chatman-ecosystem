from enum import Enum
from .refusal import Refused
class World(str,Enum): NODE="node"; PARTITION="partition"; LATENCY="latency"; LOSS="loss"; VERSION="version"; CERTIFICATE="certificate"; AMBIGUOUS_DO="ambiguous_do"
def require_complete(worlds):
    missing=set(World)-set(worlds)
    if missing: raise Refused("INCOMPLETE_FAILURE_CENSUS", ",".join(sorted(x.value for x in missing)))
    return True
