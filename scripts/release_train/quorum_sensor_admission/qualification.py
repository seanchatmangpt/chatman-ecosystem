from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .admission import AdmissionPolicy, admit_sensor
from .authority import ActionClass, admit_action
from .causality import VectorClock
from .dependency import DependencyGraph
from .errors import Refused
from .frontier import CalibrationFrontier
from .quorum import ReplicaVote, strict_majority
from .receipt import Receipt
from .sensor_model import SensorCalibration
from .standing import bounded_standing
from .strategy import score_strategies, select
from .subject import Subject
from .topology import classify
from .visibility import VisibilityObservation


@dataclass(frozen=True)
class Qualification:
    receipt: Receipt
    selected_strategy: str | None


def qualify(*, subject: Subject, model: SensorCalibration, frontier: CalibrationFrontier,
            visibility: VisibilityObservation, votes: list[ReplicaVote], clocks: dict[str, VectorClock],
            dependencies: DependencyGraph, now: datetime, policy: AdmissionPolicy = AdmissionPolicy(),
            max_observation_age_seconds: int = 300, action: ActionClass = ActionClass.SELECT) -> Qualification:
    admit_action(action)
    if action not in {ActionClass.SELECT, ActionClass.VERIFY, ActionClass.CONSTRUCT, ActionClass.OBSERVE}:
        raise Refused("INVALID_ACTION_CLASS")
    if subject != model.subject or subject != visibility.subject:
        raise Refused("SUBJECT_BINDING_MISMATCH")
    visibility.require_current(now, max_observation_age_seconds)
    admit_sensor(model, frontier, visibility, policy)
    quorum = strict_majority(subject, visibility.known_replicas, votes)
    topology = classify(votes, quorum, clocks, visibility.coverage)
    blockers = dependencies.blockers(subject)
    standing, reason = bounded_standing(topology.topology, blockers, True)
    strategy = select(score_strategies(topology, visibility.coverage, visibility.max_lag_seconds))
    if topology.topology.value == "HEALTHY" and strategy is None:
        raise Refused("NO_ADMITTED_RELEASE_STRATEGY")
    receipt = Receipt(subject=subject.canonical(), calibration_generation=model.generation,
        calibration_digest=model.digest(), coverage=f"{visibility.coverage.numerator}/{visibility.coverage.denominator}",
        topology=topology.topology.value, strategy=strategy.value if strategy else None, blockers=blockers,
        standing=standing, reason=reason).seal()
    receipt.replay()
    return Qualification(receipt=receipt, selected_strategy=receipt.strategy)
