from dataclasses import dataclass
from .admission import admit_relation, AdmissionThresholds
from .bundle import SelectionBundle
from .strongest import select_strongest_defensible
from .minimax import select_minimax
from .pareto import frontier as pareto_frontier
from .information import select_information_seeking
from .standing import classify
from .receipt import Receipt

@dataclass(frozen=True)
class Evaluation:
    admitted: tuple
    bundle: SelectionBundle
    standing: object
    receipt: Receipt | None

def evaluate(subject, frontier, metamorphic_by_relation, oracles_by_relation, *, hard_failure=False, blocked=False, thresholds=AdmissionThresholds()):
    admitted = []
    for relation in sorted(metamorphic_by_relation, key=lambda r: r.value):
        try:
            admitted.append(admit_relation(relation, frontier, metamorphic_by_relation[relation], oracles_by_relation[relation], thresholds))
        except Exception as exc:
            from .refusal import Refused
            if not isinstance(exc, Refused):
                raise
    admitted = tuple(admitted)
    relations = tuple(e.relation for e in admitted)
    pf = pareto_frontier(admitted)
    bundle = SelectionBundle(
        strongest=select_strongest_defensible(relations),
        minimax=select_minimax(admitted),
        pareto=tuple(c.evidence.relation for c in pf),
        information=select_information_seeking(admitted),
    )
    standing = classify(admitted_count=len(admitted), hard_failure=hard_failure, blocked=blocked)
    receipt = None
    if not hard_failure and not blocked and admitted:
        receipt = Receipt(
            subject=subject.key,
            generation=frontier.generation,
            strongest=tuple(r.value for r in bundle.strongest),
            standing=standing.value,
        )
    return Evaluation(admitted, bundle, standing, receipt)
