from .refusal import Refused
def admit_cases(subject,cases,now,current_generation):
    admitted=[]; seen={}
    for case in cases:
        if case.subject!=subject: raise Refused("REFUSED[FOREIGN_SUBJECT]")
        if case.stress.generation!=current_generation: raise Refused("REFUSED[STALE_STRESS_GENERATION]")
        if case.observed_at>now: raise Refused("REFUSED[FUTURE_REALIZATION]")
        prior=seen.get(case.case_id)
        if prior is not None and prior!=case: raise Refused("REFUSED[CONTRADICTORY_DUPLICATE_CASE]")
        if prior is None:
            seen[case.case_id]=case; admitted.append(case)
    return tuple(sorted(admitted))
