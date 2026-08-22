def next_standing(current, reason):
    if reason in {'PRODUCER_BUILD_BROKEN','PRODUCER_BLOCKED'}:
        return 'BLOCKED'
    if reason == 'PRODUCER_RECOVERED_REQUALIFY':
        return 'REQUALIFYING'
    return 'UNKNOWN'

def apply_standing(current_by_subject, cascade):
    return {i.subject: next_standing(current_by_subject.get(i.subject,'UNKNOWN'), i.reason) for i in cascade}
