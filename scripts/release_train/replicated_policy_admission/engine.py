from dataclasses import dataclass
from datetime import datetime
from .subject import Subject
from .replica import ReplicaPolicyState
from .lease import Lease
from .quorum import qualify_quorum
from .frontier import classify_frontier
from .policy import ExpectedPolicy,admit_expected
from .dependency import DependencyGraph
from .standing import bounded_standing
from .receipt import Receipt
from .refusal import Refused
@dataclass(frozen=True)
class Qualification:
    standing:str; reason:str; receipt:Receipt|None
def qualify(subject:Subject,states:list[ReplicaPolicyState],lease:Lease,at:datetime,expected:ExpectedPolicy,dependencies:DependencyGraph)->Qualification:
    if not lease.admits(at): raise Refused("REPLICA_LEASE_INACTIVE")
    if any(s.subject!=subject for s in states): raise Refused("FOREIGN_REPLICA_SUBJECT")
    q=qualify_quorum(states); frontier=classify_frontier(states); blockers=dependencies.blockers()
    if q.policy_digest is not None: admit_expected(q,expected)
    standing,reason=bounded_standing(q,blockers,frontier.concurrent)
    receipt=Receipt(subject.identity,q.generation,q.policy_digest,q.frontier_digest,q.agreeing,blockers,standing,reason)
    return Qualification(standing,reason,receipt)
