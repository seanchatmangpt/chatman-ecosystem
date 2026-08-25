from .errors import Refused
def support_overlap(source,target):
    s=set(source); t=set(target)
    if not t: raise Refused("REFUSED[EMPTY_TARGET_SUPPORT]")
    covered=t&s
    return {"covered":tuple(sorted(covered)),"missing":tuple(sorted(t-s)),"fraction":len(covered)/len(t)}
