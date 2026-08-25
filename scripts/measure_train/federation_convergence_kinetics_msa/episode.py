from dataclasses import dataclass
from .refusal import Refused

TERMINAL = {"FIXED", "REGRESSED", "BLOCKED"}

@dataclass(frozen=True)
class Episode:
    observations: tuple

    @property
    def episode_id(self):
        return self.observations[0].episode_id

    @property
    def subject(self):
        return self.observations[0].subject

    @property
    def duration(self):
        return self.observations[-1].step - self.observations[0].step

    @property
    def terminal_state(self):
        state = self.observations[-1].state
        return state if state in TERMINAL else "CENSORED"

def admit_episode(observations):
    rows = tuple(sorted(observations, key=lambda row: row.step))
    if not rows:
        raise Refused("EMPTY_EPISODE")
    first = rows[0]
    seen = set()
    for index, row in enumerate(rows):
        if row.subject != first.subject:
            raise Refused("FOREIGN_SUBJECT")
        if row.episode_id != first.episode_id:
            raise Refused("MIXED_EPISODE")
        if row.step in seen:
            raise Refused("DUPLICATE_STEP")
        seen.add(row.step)
        if index and row.step != rows[index - 1].step + 1:
            raise Refused("TORN_EPISODE")
        if index and row.observed_at <= rows[index - 1].observed_at:
            raise Refused("NON_MONOTONE_TIME")
        if index and rows[index - 1].state in TERMINAL:
            raise Refused("POST_TERMINAL_EVIDENCE")
    return Episode(rows)
