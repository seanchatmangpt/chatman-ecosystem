from .admission import admit_claims
from .chain import validate_chain
from .coverage import provenance_coverage
from .receipt import manufacture_receipt
from .telemetry import project_events

def qualify(subject, claims, edges, parent_receipt=None):
    admitted=admit_claims(subject,claims)
    chain=validate_chain([c.evidence_id for c in admitted],edges)
    coverage=provenance_coverage(admitted,edges)
    receipt=manufacture_receipt(subject,coverage,chain,parent_receipt)
    return {"subject":subject,"claims":admitted,"coverage":coverage,"receipt":receipt,
            "telemetry":project_events(subject,admitted,edges),"actuation_performed":False}
