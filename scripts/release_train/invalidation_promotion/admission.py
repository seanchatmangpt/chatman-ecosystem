from .subject import Refusal

def admit_event(bindings, event):
    matched=[b for b in bindings if b.producer==event.producer]
    if not matched:
        raise Refusal('REFUSED[ORPHAN_INVALIDATION_EVENT]')
    if event.kind == 'NEW_RECEIPT' and all(b.receipt == event.replacement_receipt for b in matched):
        raise Refusal('REFUSED[NON_MOVING_RECEIPT]')
    return tuple(matched)
