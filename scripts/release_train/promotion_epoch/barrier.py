REQUIRED=("narrow","unit","integration","e2e","replay","negative","exact_head")
class BarrierRefusal(ValueError): pass
def qualify_barrier(results):
    missing=[r for r in REQUIRED if r not in results]
    if missing: return "UNKNOWN", tuple(missing)
    failed=[r for r in REQUIRED if results[r] != "PASS"]
    if failed: return "BUILD_BROKEN", tuple(failed)
    return "ALIVE", ()
