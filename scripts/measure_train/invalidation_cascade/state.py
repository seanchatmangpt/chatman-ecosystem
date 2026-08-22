def classify_binding(binding, event):
    if binding.producer != event.producer:
        return "CURRENT"
    if event.kind=="RECOVERED":
        return "REQUALIFYING"
    if event.kind in {"BUILD_BROKEN","BLOCKED"}:
        return "BLOCKED"
    return "INVALIDATED"

def aggregate(states):
    values=set(states)
    if not values: return "UNKNOWN"
    if "BLOCKED" in values: return "BLOCKED"
    if "INVALIDATED" in values or "REQUALIFYING" in values: return "UNKNOWN"
    return "PARTIAL_ALIVE"
