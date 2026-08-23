from .subject import Refused

def admit_trajectory(epochs):
    rows=tuple(epochs)
    if not rows: return rows
    repo=rows[0].subject.repo
    previous=None
    for row in rows:
        if row.subject.repo != repo: raise Refused("REFUSED[CROSS_REPOSITORY_TRAJECTORY]")
        if previous is not None:
            if row.subject.generation != previous.subject.generation + 1: raise Refused("REFUSED[NON_CONTIGUOUS_GENERATION]")
            if row.observed_at <= previous.observed_at: raise Refused("REFUSED[NON_MONOTONE_EPOCH_TIME]")
            if row.subject.sha == previous.subject.sha: raise Refused("REFUSED[NOOP_SUBJECT_MOVEMENT]")
        previous=row
    return rows
