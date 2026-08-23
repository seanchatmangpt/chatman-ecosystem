from datetime import timedelta

def stable_dwell(epochs, obligation_id, target="PASS"):
    start=end=None
    for epoch in epochs:
        state=next((o.state for o in epoch.obligations if o.obligation_id==obligation_id),None)
        if state == target:
            if start is None: start=epoch.observed_at
            end=epoch.observed_at
        else:
            start=end=None
    if start is None or end is None: return timedelta(0)
    return end-start
