from .refusal import Refused
def require_independence(rows):
 if len({r.control.implementation for r in rows})<4 or len({r.control.model_digest for r in rows})<4 or len({r.control.evidence_root for r in rows})<4:
  raise Refused("REFUSED[PSEUDO_INDEPENDENT_CONTROL_EVIDENCE]")
 return True
