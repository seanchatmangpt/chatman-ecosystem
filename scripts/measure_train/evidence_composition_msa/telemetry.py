def project(subject, calibration, cut, standing_value):
    return (
      {"activity":"evidence_composition_calibrated","repo":subject.repo,"sha":subject.sha,
       "support":calibration.support,"state":calibration.state},
      {"activity":"evidence_composition_qualified","repo":subject.repo,"sha":subject.sha,
       "blocking_cut":list(cut),"standing":standing_value},
    )
