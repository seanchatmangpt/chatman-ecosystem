def first_index(rows,state='FIXED'):
    return next((i for i,r in enumerate(rows) if r.state==state),None)
def seconds(rows,state='FIXED'):
    i=first_index(rows,state); return None if i is None else (rows[i].observed_at-rows[0].observed_at).total_seconds()
