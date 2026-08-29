from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .epoch import EpochStamp
from .observation import Observation

@dataclass(frozen=True)
class EvidenceCut:
    cut_at: datetime
    epochs: tuple[EpochStamp, ...]
    observations: tuple[Observation, ...]

    def __post_init__(self) -> None:
        if self.cut_at.tzinfo is None or self.cut_at.utcoffset() is None:
            raise ValueError('REFUSED[NAIVE_CUT_TIME]')
        repos = [e.producer.repo for e in self.epochs]
        if len(repos) != len(set(repos)):
            raise ValueError('REFUSED[DUPLICATE_PRODUCER_IN_CUT]')
        epoch_by_repo = {e.producer.repo: e for e in self.epochs}
        for obs in self.observations:
            current = epoch_by_repo.get(obs.epoch.producer.repo)
            if current is None:
                raise ValueError('REFUSED[OBSERVATION_OUTSIDE_CUT]')
            if obs.epoch.identity() != current.identity():
                raise ValueError('REFUSED[TORN_CUT_OBSERVATION]')
            if obs.observed_at > self.cut_at:
                raise ValueError('REFUSED[FUTURE_CUT_OBSERVATION]')
