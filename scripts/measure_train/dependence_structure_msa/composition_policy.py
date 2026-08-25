from .subject import Refused

def composition_mode(empirical_verdict, calibration, model, provenance_audit):
    if calibration.state!="CALIBRATED" or model.calibration_state!="CALIBRATED":
        raise Refused("REFUSED[UNCALIBRATED_DEPENDENCE_MODEL]")
    if empirical_verdict=="INDEPENDENT":
        if not provenance_audit["structurally_distinct"]:
            raise Refused("REFUSED[INDEPENDENCE_WITHOUT_STRUCTURAL_DISTINCTNESS]")
        return "INDEPENDENT"
    return "UNKNOWN_DEPENDENCE"
