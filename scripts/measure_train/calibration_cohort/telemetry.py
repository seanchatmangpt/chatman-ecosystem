def project(subject, cohort, synchrony, census_rows):
    base={"activity":"measure_calibration_cohort","repo":subject.repo,"sha":subject.sha,
          "common_micros":synchrony.common_micros,"overlap_n":synchrony.overlap.numerator,"overlap_d":synchrony.overlap.denominator}
    return tuple(dict(base,source=source,state=state,generation=cohort.by_source()[source].generation) for source,state in census_rows)
