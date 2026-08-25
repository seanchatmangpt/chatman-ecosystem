def effective_capital(rows):
 return len({(r.control.implementation,r.control.model_digest,r.control.evidence_root) for r in rows})
