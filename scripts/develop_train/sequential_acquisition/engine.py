from dataclasses import dataclass
from .authority import ActionClass, admit_action
from .bayes import update
from .belief import BeliefState
from .budget import BudgetState
from .evidence import ObservationEvidence
from .information import InformationRealization, realized_information
from .policy import Candidate, select
from .receipt import Receipt
from .stopping import StopRule
from .subject import Subject

@dataclass(frozen=True)
class Transition:
    belief: BeliefState
    budget: BudgetState
    information: InformationRealization
    receipt: Receipt


def advance(subject: Subject, prior: BeliefState, budget: BudgetState, evidence: ObservationEvidence, *, predicted_bits: float, step: int) -> Transition:
    posterior = update(prior, evidence)
    remaining = budget.consume(evidence)
    info = realized_information(prior, posterior, predicted_bits)
    receipt = Receipt(subject.value, step, posterior.generation, None, "PARTIAL_ALIVE")
    return Transition(posterior, remaining, info, receipt)

def plan_next(subject: Subject, belief: BeliefState, budget: BudgetState, candidates: list[Candidate], strategy: str, stop_rule: StopRule, step: int) -> Receipt:
    admit_action(ActionClass.SELECT)
    if stop_rule.should_stop(belief, budget, step):
        return Receipt(subject.value, step, belief.generation, None, "PARTIAL_ALIVE")
    chosen = select(candidates, budget, strategy)
    return Receipt(subject.value, step, belief.generation, chosen.candidate_id, "UNKNOWN")
