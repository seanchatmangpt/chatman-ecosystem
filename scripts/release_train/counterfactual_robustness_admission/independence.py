from .refusal import refuse

def require_independent(a,b,proof_pairs):
    pair=tuple(sorted((a.estimator_id,b.estimator_id)))
    if pair not in {tuple(sorted(x)) for x in proof_pairs}: refuse("INDEPENDENCE_UNPROVEN")
    if a.implementation_digest==b.implementation_digest: refuse("CORRELATED_ESTIMATORS")
    if a.model_digest and b.model_digest and a.model_digest==b.model_digest: refuse("CORRELATED_ESTIMATORS")
    return True
