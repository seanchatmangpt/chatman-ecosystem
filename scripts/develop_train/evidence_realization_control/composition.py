from .provenance import require_distinct_provenance
def compose(a,b,independent=False):
    if independent:
        require_distinct_provenance(a,b)
        return a.interval.independent_and(b.interval)
    return a.interval.frechet_and(b.interval)
