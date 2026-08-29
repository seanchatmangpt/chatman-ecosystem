from .horizon import HorizonState
def classify(*,step,policy,confidence,budget,calibration_ok,current,blockers,debt):
    if blockers: return HorizonState.BLOCKED
    if not current: return HorizonState.STALE
    if not calibration_ok: return HorizonState.DRIFTED
    if confidence>=policy.confidence: return HorizonState.SATISFIED
    if step>=policy.max_steps or budget.samples==0: return HorizonState.EXHAUSTED
    if not debt.within(max_information=policy.max_information_debt,max_cost_slip=policy.max_cost_slip,max_latency_slip=policy.max_latency_slip): return HorizonState.EXHAUSTED
    return HorizonState.ACQUIRING if step else HorizonState.READY
