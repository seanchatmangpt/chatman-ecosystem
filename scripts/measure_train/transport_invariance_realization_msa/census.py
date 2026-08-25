from collections import Counter
def census(cases):
    rows=tuple(cases); states=Counter("SUCCESS" if c.observed_success else "FAILURE" for c in rows); stress=Counter(c.stress.kind for c in rows)
    return {"support":len(rows),"success":states["SUCCESS"],"failure":states["FAILURE"],"stress_kinds":dict(sorted(stress.items()))}
