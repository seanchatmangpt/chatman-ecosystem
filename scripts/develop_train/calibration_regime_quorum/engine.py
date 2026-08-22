from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .admission import RecoveryWitness,admit_witness
from .authority_receipt import ActionClass,QualificationReceipt,require_action
from .decision import decide
from .frontier import RegimeFrontier
from .independence import EvidenceSource,IndependenceProof,independent_cluster_count
from .information import contribution
from .persistence import PersistenceNeed,select_store
from .standing import bounded_standing
from .subject import Subject
@dataclass(frozen=True,slots=True)
class Qualification:
    standing:str; receipt:QualificationReceipt; statistic:float; independent_clusters:int
def qualify(*,subject:Subject,witnesses:tuple[RecoveryWitness,...],frontiers:dict[str,RegimeFrontier],sources:dict[str,EvidenceSource],proofs:tuple[IndependenceProof,...],dependency_standings:dict[str,str],now:datetime,persistence_need:PersistenceNeed=PersistenceNeed(),required_clusters:int=2)->Qualification:
    require_action(ActionClass.CONSTRUCT); contributions=[]; used_sources=[]; outcomes=[]; generations=[]
    for witness in witnesses:
        frontier=frontiers[witness.source_id]; admit_witness(witness,frontier,now=now); model=frontier.current.model
        assert model is not None
        contributions.append(contribution(model,witness)); used_sources.append(sources[witness.source_id]); outcomes.append(witness.outcome); generations.append((witness.source_id,frontier.current.generation))
    decision=decide(tuple(contributions)); independent=independent_cluster_count(tuple(used_sources),proofs)
    standing=bounded_standing(decision=decision,independent_clusters=independent,required_clusters=required_clusters,outcomes=tuple(outcomes),dependency_standings=dependency_standings)
    store=select_store(persistence_need); receipt=QualificationReceipt(subject=subject,regime_generations=tuple(sorted(generations)),decision=decision.result,standing=standing.standing,store=store.selected,blockers=standing.blockers)
    return Qualification(standing.standing,receipt,decision.statistic,independent)
