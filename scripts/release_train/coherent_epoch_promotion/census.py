from __future__ import annotations
from dataclasses import dataclass
from .observation import Observation, Outcome, Scope
from .subject import Subject

@dataclass(frozen=True)
class CensusRow:
    subject: Subject
    state: str

def census(subjects: tuple[Subject, ...], observations: tuple[Observation, ...]) -> tuple[CensusRow, ...]:
    by_subject: dict[Subject, list[Observation]] = {s: [] for s in subjects}
    for obs in observations:
        if obs.consumer in by_subject:
            by_subject[obs.consumer].append(obs)
    rows: list[CensusRow] = []
    for subject in subjects:
        rows_obs = by_subject[subject]
        outcomes = {o.outcome for o in rows_obs}
        scopes = {o.scope for o in rows_obs}
        if Outcome.FAIL in outcomes: state='BUILD_BROKEN'
        elif not rows_obs or Outcome.UNKNOWN in outcomes or Outcome.PENDING in outcomes: state='UNKNOWN'
        elif outcomes == {Outcome.UNSUPPORTED}: state='UNSUPPORTED'
        elif Outcome.PASS in outcomes and Scope.REPOSITORY in scopes: state='PARTIAL_ALIVE'
        elif Outcome.PASS in outcomes: state='UNKNOWN'
        else: state='UNKNOWN'
        rows.append(CensusRow(subject, state))
    return tuple(rows)
