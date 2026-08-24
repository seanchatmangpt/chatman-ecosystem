from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused

@dataclass(frozen=True)
class EffectiveEpisodes:
    nominal: int
    cause_units: int
    root_units: int
    effective: int
    ratio: Fraction

def effective_episodes(episodes):
    rows = tuple(episodes)
    if not rows:
        raise Refused("EMPTY_EPISODES")
    causes = {episode.observations[0].common_cause for episode in rows}
    roots = {episode.observations[0].evidence_root for episode in rows}
    effective = min(len(rows), len(causes), len(roots))
    return EffectiveEpisodes(len(rows), len(causes), len(roots), effective, Fraction(effective, len(rows)))
