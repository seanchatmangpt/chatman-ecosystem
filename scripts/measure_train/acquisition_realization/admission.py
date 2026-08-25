from .subject import Refused

def admit_realization(plan, outcome, current_policy_generation, current_frontier_digest, now):
    if plan.subject != outcome.subject:
        raise Refused("REFUSED[FOREIGN_OUTCOME_SUBJECT]")
    if plan.plan_id != outcome.plan_id or plan.candidate_id != outcome.candidate_id:
        raise Refused("REFUSED[FOREIGN_OUTCOME_PLAN]")
    if plan.policy_generation != current_policy_generation:
        raise Refused("REFUSED[STALE_ACQUISITION_POLICY]")
    if plan.frontier_digest != current_frontier_digest:
        raise Refused("REFUSED[STALE_ACQUISITION_FRONTIER]")
    if now.tzinfo is None or now.utcoffset() is None:
        raise Refused("REFUSED[NAIVE_NOW]")
    if outcome.observed_at > now:
        raise Refused("REFUSED[FUTURE_OUTCOME]")
    return "ADMITTED"
