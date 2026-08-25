def fixed_dwell_seconds(rows):
    start=end=None
    for r in rows:
        if r.state=='FIXED' and r.blocker_count==0 and r.error_mass==0:
            if start is None: start=r.observed_at
            end=r.observed_at
        else: start=end=None
    return 0 if start is None else (end-start).total_seconds()
