from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .likelihood import LikelihoodContribution


@dataclass(frozen=True, slots=True)
class SequentialDecision:
    statistic: Decimal
    decision: str


def decide(
    contributions: tuple[LikelihoodContribution, ...],
    *,
    accept_threshold: Decimal = Decimal("2"),
    reject_threshold: Decimal = Decimal("-2"),
) -> SequentialDecision:
    if reject_threshold >= accept_threshold:
        raise ValueError("REFUSED[INVALID_SEQUENTIAL_THRESHOLDS]")
    statistic = sum((c.value for c in contributions), Decimal("0"))
    if statistic >= accept_threshold:
        decision = "ACCEPT_BOUNDED"
    elif statistic <= reject_threshold:
        decision = "REJECT"
    else:
        decision = "CONTINUE"
    return SequentialDecision(statistic, decision)
