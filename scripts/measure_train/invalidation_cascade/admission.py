from .subject import Refused

def admit_event(bindings, event):
    matched=[b for b in bindings if b.producer == event.producer]
    if not matched:
        raise Refused("REFUSED[ORPHAN_INVALIDATION_EVENT]")
    if event.kind=="NEW_RECEIPT" and not event.replacement_receipt:
        raise Refused("REFUSED[MISSING_REPLACEMENT_RECEIPT]")
    return tuple(sorted(matched))
