from .admission import admit_observations
from .contingency import contingency
from .association import association
from .information import profile
from .exact_test import exact_permutation_p_value
from .verdict import classify
from .provenance import audit
from .composition_policy import composition_mode
from .bounded_standing import standing
from .receipt import manufacture

def qualify_pair(subject, observations, now, calibration, model, provenance_claim, dependency_states=()):
    rows=admit_observations(subject,observations,now)
    table=contingency(rows)
    assoc=association(table)
    info=profile(table)
    p=exact_permutation_p_value(rows)
    verdict=classify(table.n,assoc.absolute_phi,info.mutual_information_bits,p)
    prov=audit(provenance_claim,verdict)
    mode=composition_mode(verdict,calibration,model,prov) if verdict!="INSUFFICIENT" else "UNKNOWN_DEPENDENCE"
    status=standing([verdict],calibration,dependency_states)
    pair=tuple(sorted((provenance_claim.left_id,provenance_claim.right_id)))+(verdict,mode)
    receipt=manufacture(subject,(pair,),calibration,status)
    telemetry=({
      "activity":"measure_dependence_structure",
      "repo":subject.repo,"sha":subject.sha,
      "left":pair[0],"right":pair[1],"verdict":verdict,"composition_mode":mode,
      "phi":assoc.phi,"mutual_information_bits":info.mutual_information_bits,"p_value":p,
    },)
    return {"verdict":verdict,"mode":mode,"standing":status,"receipt":receipt,"telemetry":telemetry,"actuation_performed":False}
