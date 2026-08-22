from __future__ import annotations
from dataclasses import dataclass
from .authority import ActionClass, admit_action
from .budget import EvidenceBudget
from .consensus import Consensus, decide
from .cusum import detect as cusum_detect
from .detector_vote import DetectorVote
from .ewma import detect as ewma_detect
from .hysteresis import HysteresisState, advance
from .independence import IndependenceProof
from .page_hinkley import detect as ph_detect
from .receipt import QualificationReceipt, issue
from .sample import ErrorSample
from .standing import Standing, bounded_standing
from .subject import Subject
from .window import SampleWindow

@dataclass(frozen=True)
class Qualification:
    consensus: Consensus
    hysteresis: HysteresisState
    standing: Standing
    receipt: QualificationReceipt
    digest: str

def qualify(subject: Subject, samples: list[ErrorSample], window: SampleWindow, proofs: list[IndependenceProof], prior: HysteresisState, dependency: Standing, budget: EvidenceBudget, action: ActionClass = ActionClass.SELECT) -> Qualification:
    admit_action(action)
    selected = window.select(samples)
    c = cusum_detect(selected, target=0.2, slack=0.05, threshold=0.8)
    p = ph_detect(selected, delta=0.02, threshold=0.45)
    e = ewma_detect(selected, baseline=0.2, alpha=0.4, threshold=0.35)
    votes = [
        DetectorVote("cusum", "cumulative-sum", "sequential", c.changed, c.score),
        DetectorVote("page-hinkley", "mean-shift", "online-mean", p.changed, p.statistic),
        DetectorVote("ewma", "exponential-smoother", "weighted-state", e.changed, abs(e.level-0.2)),
    ]
    budget.admit(len(selected), len(votes), sum(v.score for v in votes))
    consensus = decide(votes, proofs, required=2)
    hysteresis = advance(prior, consensus.changed)
    standing = bounded_standing(hysteresis.state, dependency, evidence_current=not consensus.changed)
    receipt, digest = issue(subject, hysteresis.state.value, consensus.detectors, standing.name)
    return Qualification(consensus, hysteresis, standing, receipt, digest)
