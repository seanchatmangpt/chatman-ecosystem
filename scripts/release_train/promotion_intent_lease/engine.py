from dataclasses import dataclass
from datetime import datetime
from .admission import admit_intent
from .authority import ActionClass, require
from .candidate import PersistenceNeed, select
from .dependency import DependencyGraph
from .frontier import PromotionFrontier
from .intent import PromotionIntent
from .lease import IntentLease
from .plan import PromotionPlan
from .receipt import Receipt
from .standing import aggregate

@dataclass(frozen=True)
class Qualification:
    standing: str
    store: str
    plan: PromotionPlan
    receipt: Receipt

def qualify(intent: PromotionIntent, lease: IntentLease, frontier: PromotionFrontier, now: datetime,
            graph: DependencyGraph, outcomes: tuple[str,...], need: PersistenceNeed) -> Qualification:
    admit_intent(intent, lease, frontier, now)
    require(ActionClass.CONSTRUCT)
    order=graph.closure(intent.consumer)
    st=aggregate(outcomes).value
    store=select(need).value
    plan=PromotionPlan(order)
    receipt=Receipt.manufacture({'intent':intent.identity(),'standing':st,'store':store,'subjects':[str(x) for x in order],'phases':list(plan.phases)})
    return Qualification(st,store,plan,receipt)
