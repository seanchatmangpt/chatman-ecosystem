from .refusal import Refused

def current_transport_frontier(observations):
    by={}
    for row in observations:
        key=row.transport.name
        old=by.get(key)
        if old is None or row.transport.generation > old.transport.generation:
            by[key]=row
        elif row.transport.generation == old.transport.generation:
            if row.transport != old.transport:
                raise Refused("REFUSED[DIVERGENT_TRANSPORT_FRONTIER]")
            if row.observed_at > old.observed_at:
                by[key]=row
    return tuple(sorted(by.values(),key=lambda r:r.transport.name))
