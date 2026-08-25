from .subject import Refused
from .validator import provenance_distinct
from .overlap import ancestry_overlap
def admit_independence(graph,left,right,stats,calibration,model,max_abs_phi=0.05,max_mi=0.01):
    if not provenance_distinct(left,right): raise Refused("REFUSED[SHARED_VALIDATOR_PROVENANCE]")
    if ancestry_overlap(graph,left.evidence_id,right.evidence_id)!=0: raise Refused("REFUSED[SHARED_EVIDENCE_ANCESTRY]")
    if stats.support<calibration.support: raise Refused("REFUSED[INSUFFICIENT_EMPIRICAL_SUPPORT]")
    if abs(stats.phi)>max_abs_phi or stats.mutual_information>max_mi: raise Refused("REFUSED[EMPIRICAL_DEPENDENCE]")
    if calibration.state!="CALIBRATED" or model.state!="CALIBRATED": raise Refused("REFUSED[UNCALIBRATED_INDEPENDENCE]")
    return "INDEPENDENCE_ADMITTED"
