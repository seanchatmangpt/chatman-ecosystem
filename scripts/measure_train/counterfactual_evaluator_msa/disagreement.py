from fractions import Fraction
from collections import defaultdict

def estimator_disagreement(cases):
    by_case=defaultdict(list)
    for c in cases: by_case[c.case_id].append(c.estimate)
    diameters=[]
    for vals in by_case.values():
        if len(vals)>=2: diameters.append(max(vals)-min(vals))
    return Fraction(0) if not diameters else sum(diameters,Fraction(0))/len(diameters)
