import hashlib
import json

ROUTES = {
    "R_missing_identity": "ExactSubjectRepair",
    "R_missing_replay": "ReplayRepair",
    "R_missing_authority": "AuthorityRepair",
    "R_missing_consequence": "ConsequenceRepair",
    "mu_on_O": "ManufactureRepair",
    "R_not_fed_back": "FeedbackRepair",
}

def _hash(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()

def manufacture(subject, terms):
    if len(subject) != 40 or any(c not in "0123456789abcdef" for c in subject):
        raise ValueError("REFUSED:MUTABLE_SUBJECT")
    unknown = sorted(set(terms) - set(ROUTES))
    if unknown:
        raise ValueError("REFUSED:UNKNOWN_FINDING")
    demands = []
    for term in sorted(set(terms)):
        item = {"subject": subject, "broken_term": term, "capability": ROUTES[term], "authority": "NONE", "standing": "CANDIDATE"}
        item["demand_id"] = _hash(item)
        demands.append(item)
    receipt = {"subject": subject, "authority": "NONE", "demands": demands}
    receipt["receipt_digest"] = _hash(receipt)
    return receipt

def replay(receipt):
    rebuilt = manufacture(receipt["subject"], [d["broken_term"] for d in receipt["demands"]])
    return rebuilt["receipt_digest"] == receipt["receipt_digest"]
