from .refusal import Refused
def result_correspondence(rows):
 passing=[r for r in rows if r.state=="PASS"]; fam={r.control.family:r.result_digest for r in passing}
 if len(fam)<4: raise Refused("REFUSED[INCOMPLETE_CONTROL_FAMILY_COVERAGE]")
 if len(set(fam.values()))!=1: raise Refused("REFUSED[CROSS_CONTROL_RESULT_DIVERGENCE]")
 return next(iter(fam.values()))
