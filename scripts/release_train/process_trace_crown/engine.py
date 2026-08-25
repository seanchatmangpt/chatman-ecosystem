from __future__ import annotations
from dataclasses import dataclass
from .authority import ActionClass, admit as admit_action
from .bisimulation import witness
from .failure import Failure, require_complete as require_failures
from .methodology import require_complete as require_methods
from .oracle import OracleWitness, require_independent
from .rail import RailEvidence, admit as admit_rails
from .receipt import Receipt
from .relation import Relation
from .standing import Standing, compute
from .trace import Trace

@dataclass(frozen=True)
class Qualification:
    standing: Standing
    receipt: Receipt | None

def qualify(reference: Trace, candidate: Trace, *, relation: Relation, fuel: int, oracle_witnesses: tuple[OracleWitness,...], rails: tuple[RailEvidence,...], methodologies: set[str], failures: set[Failure], blockers: set[str], action: ActionClass = ActionClass.SELECT) -> Qualification:
    admit_action(action)
    require_independent(oracle_witnesses)
    admit_rails(rails)
    require_methods(methodologies)
    require_failures(failures)
    corr = witness(reference, candidate, relation, fuel).accepted
    states = [r.state for r in rails]
    standing = compute(states, blockers, corr, True)
    receipt = None if standing in {Standing.BUILD_BROKEN, Standing.BLOCKED, Standing.UNKNOWN} else Receipt(reference.subject.key, candidate.digest, standing.value)
    return Qualification(standing, receipt)
