from .refusal import refuse
def require_tls_regions(records):
    records=list(records)
    if len({r["host"] for r in records})<2 or len({r["region"] for r in records})<2:
        refuse("INSUFFICIENT_REGION_INDEPENDENCE")
    if any(not r.get("encrypted") or not r.get("certificate") for r in records):
        refuse("TLS_EVIDENCE_INVALID")
    if len({r.get("generation") for r in records})!=1:
        refuse("DIVERGENT_REGION_GENERATION")
    return True
