from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, getcontext
from fractions import Fraction

from .calibration_model import CalibrationModel

getcontext().prec = 34


@dataclass(frozen=True, slots=True)
class LikelihoodContribution:
    source_id: str
    outcome: str
    value: Decimal


def _decimal(frac: Fraction) -> Decimal:
    return Decimal(frac.numerator) / Decimal(frac.denominator)


def contribution(model: CalibrationModel, outcome: str) -> LikelihoodContribution:
    if outcome in {"PENDING", "UNKNOWN", "UNSUPPORTED"}:
        return LikelihoodContribution(model.source_id, outcome, Decimal("0"))
    if outcome not in {"PASS", "FAIL"}:
        raise ValueError("REFUSED[INVALID_LIKELIHOOD_OUTCOME]")
    tpr, fpr = _decimal(model.true_positive_rate), _decimal(model.false_positive_rate)
    if outcome == "PASS":
        ratio = tpr / fpr
    else:
        ratio = (Decimal(1) - tpr) / (Decimal(1) - fpr)
    return LikelihoodContribution(model.source_id, outcome, ratio.ln())
