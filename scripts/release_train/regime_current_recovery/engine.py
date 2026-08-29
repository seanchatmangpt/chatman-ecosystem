from dataclasses import dataclass
from datetime import datetime
from .admission import admit_current
from .authority import ActionClass, require
from .dependencies import DependencyGraph
from .frontier import RegimeFrontier
from .independence import Relation, clusters, relation
from .information import contribution, sequential_decision
from .persistence import PersistenceNeed, candidates, select
from .receipt import Receipt, manufacture, replay
from .standing import bounded_standing
from .evidence import RecoveryWitness
from .subject import Subject

@dataclass(frozen=True)
class Qualification:
    standing: str
    reason: str
    decision: str
    statistic: float
    store: str
    alternatives: tuple[str,...]
    phases: tuple[str,...]
    receipt: Receipt

def qualify(root: Subject, witnesses: list[RecoveryWitness], frontiers: dict[str,RegimeFrontier], graph: DependencyGraph, dependency_standing: dict[Subject,str], now: datetime, explicit_pairs: set[frozenset[str]]|None=None, persistence_need: PersistenceNeed=PersistenceNeed()) -> Qualification:
    require(ActionClass.CONSTRUCT)
    blockers=graph.blockers(root,dependency_standing)
    current=[]; contributions=[]
    for witness in witnesses:
        frontier=frontiers[witness.source_id]; admit_current(witness,frontier,now)
        current.append(witness); contributions.append(contribution(frontier.current.model,witness.outcome))
    cluster_sets=clusters(current,explicit_pairs); representatives=[group[0].source for group in cluster_sets]
    proven=sum(all(i==j or relation(source,other,explicit_pairs)==Relation.INDEPENDENT for j,other in enumerate(representatives)) for i,source in enumerate(representatives))
    decision,statistic=sequential_decision(contributions)
    standing=bounded_standing([w.outcome for w in current],decision,proven,blockers,True)
    store=select(persistence_need)
    body={'subject':root.exact,'standing':standing.standing,'reason':standing.reason,'decision':decision,'statistic':statistic,'regimes':{k:v.current.generation for k,v in sorted(frontiers.items())},'blockers':[b.exact for b in blockers],'store':store.value,'alternatives':[s.value for s in candidates()],'phases':['VERIFY','CONSTRUCT']}
    receipt=manufacture(body); assert replay(receipt)
    return Qualification(standing.standing,standing.reason,decision,statistic,store.value,tuple(s.value for s in candidates()),('VERIFY','CONSTRUCT'),receipt)
