from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .admission import admit_witness
from .authority import ActionClass, require_nonconsequential
from .calibration_model import CalibrationModel
from .dependency import DependencyGraph
from .evidence_source import EvidenceSource
from .independence import IndependenceProof, Relation, correlated_clusters, relation
from .likelihood import contribution
from .persistence import PersistenceNeed, select_store
from .receipt import QualificationReceipt
from .sequential import decide
from .standing import bounded_standing
from .subject import Subject
from .witness import RecoveryWitness


@dataclass(frozen=True, slots=True)
class Qualification:
    standing: str
    decision: str
    receipt: QualificationReceipt


def qualify(
    *,
    subject: Subject,
    attempt_id: str,
    sources: tuple[EvidenceSource, ...],
    witnesses: tuple[RecoveryWitness, ...],
    calibrations: dict[str, CalibrationModel],
    proofs: tuple[IndependenceProof, ...],
    now: datetime,
    min_trials: int,
    required_clusters: int,
    dependency_graph: DependencyGraph,
    dependency_standings: dict[str, str],
    dependency_root: str,
    persistence: PersistenceNeed,
    action: ActionClass = ActionClass.CONSTRUCT,
) -> Qualification:
    require_nonconsequential(action)
    if len(sources) != len({source.fingerprint for source in sources}):
        raise ValueError("REFUSED[DUPLICATE_EVIDENCE_SOURCE]")
    source_by_id = {source.fingerprint: source for source in sources}
    admitted: list[RecoveryWitness] = []
    under_calibrated = False
    for witness in witnesses:
        model = calibrations.get(witness.source_fingerprint)
        if model is None:
            under_calibrated = True
            continue
        ok, reason = admit_witness(
            witness,
            attempt_id=attempt_id,
            now=now,
            calibration=model,
            min_trials=min_trials,
        )
        if ok:
            admitted.append(witness)
        elif reason == "REFUSED[UNDER_CALIBRATED_SOURCE]":
            under_calibrated = True
        else:
            raise ValueError(reason)
    contributions = tuple(
        contribution(calibrations[witness.source_fingerprint], witness.outcome)
        for witness in admitted
    )
    sequential = decide(contributions)
    clusters = correlated_clusters(
        tuple(source_by_id[witness.source_fingerprint] for witness in admitted),
        proofs,
    )
    representatives = [source_by_id[cluster[0]] for cluster in clusters]
    independent_clusters = 0
    for index, left in enumerate(representatives):
        if all(
            relation(left, right, proofs) is Relation.INDEPENDENT
            for right in representatives[index + 1 :]
        ):
            independent_clusters += 1
    if representatives:
        independent_clusters = min(independent_clusters + 1, len(representatives))
    blockers = dependency_graph.blockers(dependency_root, dependency_standings)
    outcomes = tuple(witness.outcome for witness in admitted)
    standing = (
        "BLOCKED"
        if blockers
        else bounded_standing(
            outcomes=outcomes,
            decision=sequential.decision,
            independent_clusters=independent_clusters,
            required_clusters=required_clusters,
            under_calibrated=under_calibrated,
        )
    )
    store = select_store(persistence)
    receipt = QualificationReceipt(
        subject.exact,
        attempt_id,
        tuple(sorted(witness.source_fingerprint for witness in admitted)),
        independent_clusters,
        format(sequential.statistic, "f"),
        sequential.decision,
        blockers,
        store.value,
        standing,
    )
    return Qualification(standing, sequential.decision, receipt)
