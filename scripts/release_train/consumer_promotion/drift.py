def classify(claim_receipt:str, current_receipt:str, claim_schema:str, current_schema:str, lease_active:bool)->str:
    if claim_receipt != current_receipt: return "SUPERSEDED_RECEIPT"
    if claim_schema != current_schema: return "SCHEMA_DRIFT"
    if not lease_active: return "LEASE_EXPIRED"
    return "CURRENT"
