from .subject import Refused

def resolve_epoch_frontier(epochs):
    by_producer={}
    for e in sorted(epochs):
        old=by_producer.get(e.producer)
        if old is None or e.generation > old.generation:
            by_producer[e.producer]=e
        elif e.generation == old.generation and (e.event_id != old.event_id or e.receipt_sha256 != old.receipt_sha256):
            raise Refused("REFUSED[DIVERGED_CURRENT_EPOCH]")
    return {p:by_producer[p] for p in sorted(by_producer)}
