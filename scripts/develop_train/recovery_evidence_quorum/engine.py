from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .authority import ActionClass, require_nonconsequential
from .dependencies import DependencyGraph
from .diversity import effective_source_diversity
from .evidence import RecoveryWitness
from .frontier import WitnessFrontier
from .independence import IndependenceEvidence, correlated_clusters
from .policy import QuorumPolicy, Standing, evaluate_quorum
from .provenance import ProvenanceGraph
from .receipt import QualificationReceipt
from .recovery import RecoveryAttempt
from .storage import PersistenceNeed, select_store


@dataclass(frozen=True, slots=True)
class Qualification:
    standing: Standing
    receipt: QualificationReceipt


def qualify_recovery(
    attempt: RecoveryAttempt,
    witnesses: tuple[RecoveryWitness, ...],
    *,
    now: datetime,
    provenance: ProvenanceGraph,
    independence: tuple[IndependenceEvidence, ...],
    policy: QuorumPolicy,
    dependencies: DependencyGraph,
    dependency_standings: dict[str, Standing],
    persistence: PersistenceNeed = PersistenceNeed(),
    action: ActionClass = ActionClass.CONSTRUCT,
) -> Qualification:
    require_nonconsequential(action)
    frontier = WitnessFrontier.build(attempt, witnesses, now)
    clusters = correlated_clusters(frontier.current, provenance, independence)
    standing = evaluate_quorum(policy, frontier.current, clusters)
    blockers = dependencies.blockers(attempt.consumer.exact_id, dependency_standings)
    if blockers:
        standing = Standing.BLOCKED
    diversity = effective_source_diversity(clusters)
    store = select_store(persistence)
    receipt = QualificationReceipt(
        subject=attempt.consumer.exact_id,
        attempt_id=attempt.attempt_id,
        standing=standing,
        clusters=clusters,
        diversity=f"{diversity.numerator}/{diversity.denominator}",
        blockers=blockers,
        store=store.value,
        action=action.value,
    )
    return Qualification(standing, receipt)
