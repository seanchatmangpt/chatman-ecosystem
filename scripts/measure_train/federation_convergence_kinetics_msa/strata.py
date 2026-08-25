from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused

@dataclass(frozen=True)
class StratumRisk:
    key: tuple
    support: int
    terminal_failure: Fraction

def worst_stratum(episodes):
    rows = tuple(episodes)
    if not rows:
        raise Refused("EMPTY_STRATA")
    groups = {}
    for episode in rows:
        observation = episode.observations[0]
        key = (observation.methodology, observation.engine, observation.region, observation.evidence_root)
        groups.setdefault(key, []).append(episode)
    risks = []
    for key, members in groups.items():
        failures = sum(1 for episode in members if episode.terminal_state in {"REGRESSED", "BLOCKED"})
        risks.append(StratumRisk(key, len(members), Fraction(failures, len(members))))
    return max(risks, key=lambda risk: (risk.terminal_failure, -risk.support, risk.key))
