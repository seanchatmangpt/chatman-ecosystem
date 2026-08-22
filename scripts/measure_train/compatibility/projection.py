def ocel(vector):
    return tuple(sorted((r.observed_at, vector.subject.repo, vector.subject.sha, r.axis.value, r.outcome.value) for r in vector.rows))
