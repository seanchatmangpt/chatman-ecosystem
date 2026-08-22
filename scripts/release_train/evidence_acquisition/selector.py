from dataclasses import dataclass

from .belief import Belief
from .budget import AcquisitionBudget
from .calibration import SensorCalibration
from .candidate import EvidenceCandidate
from .independence import IndependenceProof, admitted_independent
from .information import binary_entropy, expected_information_gain, pass_probability, posterior_defect
from .strategy import Strategy

@dataclass(frozen=True)
class CandidateScore:
    candidate: EvidenceCandidate
    score: float


def _score(strategy: Strategy, belief: Belief, candidate: EvidenceCandidate, calibration: SensorCalibration) -> float:
    gain = expected_information_gain(belief, calibration)
    if strategy is Strategy.MAX_INFORMATION_GAIN:
        return gain
    if strategy is Strategy.MAX_INFORMATION_PER_COST:
        return gain / max(candidate.cost_milli, 1)
    p_pass = pass_probability(belief, calibration)
    expected = float(p_pass) * binary_entropy(posterior_defect(belief, calibration, "PASS"))
    expected += float(1 - p_pass) * binary_entropy(posterior_defect(belief, calibration, "FAIL"))
    return -expected


def select(
    belief: Belief,
    candidates: tuple[EvidenceCandidate, ...],
    calibrations: tuple[SensorCalibration, ...],
    proofs: tuple[IndependenceProof, ...],
    budget: AcquisitionBudget,
    strategy: Strategy,
) -> tuple[EvidenceCandidate, ...]:
    by_id = {item.candidate_id: item for item in calibrations}
    scored = sorted(
        (CandidateScore(candidate, _score(strategy, belief, candidate, by_id[candidate.id])) for candidate in candidates if candidate.id in by_id),
        key=lambda item: (-item.score, item.candidate.id),
    )
    selected: list[EvidenceCandidate] = []
    for item in scored:
        candidate = item.candidate
        if all(admitted_independent(candidate, existing, proofs) for existing in selected):
            trial = tuple(selected + [candidate])
            try:
                budget.admit(trial)
            except ValueError:
                continue
            selected.append(candidate)
    if not selected:
        raise ValueError("REFUSED[NO_ADMISSIBLE_EVIDENCE_SELECTION]")
    return tuple(selected)
