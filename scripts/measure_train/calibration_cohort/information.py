from fractions import Fraction
def cohort_information(synchrony, epochs):
    total_support=sum(e.support for e in epochs)
    min_support=min((e.support for e in epochs), default=0)
    concentration=Fraction(min_support*len(epochs), total_support) if total_support else Fraction(0,1)
    return {"temporal_overlap":synchrony.overlap,"support_balance":concentration,"common_micros":synchrony.common_micros}
