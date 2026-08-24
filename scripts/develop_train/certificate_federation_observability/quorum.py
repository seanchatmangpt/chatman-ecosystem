from dataclasses import dataclass
from .observation import Relation
from .transport import TransportState
from .errors import Refused
@dataclass(frozen=True)
class Quorum: generation:int; certificate_digest:str; votes:int; transports:tuple[str,...]
def exact_quorum(observations,min_votes=2):
    good=[o for o in observations if o.state==TransportState.RESOLVED and o.relation in {Relation.EXACT,Relation.ADVANCED}]
    if len(good)<min_votes: raise Refused("INSUFFICIENT_EXACT_QUORUM")
    if len({o.certificate_generation for o in good})!=1: raise Refused("SPLIT_GENERATION")
    if len({o.certificate_digest for o in good})!=1: raise Refused("SPLIT_CERTIFICATE_DIGEST")
    tids=tuple(sorted({o.transport_id for o in good}))
    if len(tids)<min_votes: raise Refused("DUPLICATE_TRANSPORT_QUORUM")
    return Quorum(good[0].certificate_generation,good[0].certificate_digest,len(tids),tids)
