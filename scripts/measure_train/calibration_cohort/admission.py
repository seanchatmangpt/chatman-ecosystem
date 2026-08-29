from fractions import Fraction
from .subject import Refused
from .synchrony import measure_synchrony
def admit_cohort(cohort, frontier, min_support=1, min_overlap=Fraction(1,2), max_skew_micros=3_600_000_000):
    current={e.source:e for e in frontier}
    schemas={e.schema.fingerprint for e in cohort.epochs}
    if len(schemas)!=1: raise Refused("REFUSED[CALIBRATION_SCHEMA_MISMATCH]")
    for e in cohort.epochs:
        if current.get(e.source)!=e: raise Refused("REFUSED[STALE_CALIBRATION_EPOCH]")
        if e.state=="DRIFT": raise Refused("REFUSED[CALIBRATION_DRIFTED]")
        if e.state!="STABLE" or e.support<min_support: raise Refused("REFUSED[INSUFFICIENT_CALIBRATION]")
    s=measure_synchrony(cohort.epochs)
    if s.common_micros<=0: raise Refused("REFUSED[NO_COMMON_CALIBRATION_WINDOW]")
    if s.overlap<min_overlap: raise Refused("REFUSED[INSUFFICIENT_TEMPORAL_OVERLAP]")
    if s.max_end_skew_micros>max_skew_micros: raise Refused("REFUSED[CALIBRATION_SKEW_EXCEEDED]")
    return s
