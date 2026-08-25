from enum import Enum
from .trace import Trace
class Profile(str,Enum): EXACT="EXACT"; ACTIVITY="ACTIVITY"; STUTTER="STUTTER"
def exact(t:Trace): return tuple((e.activity,e.object_id,e.lifecycle) for e in t.events)
def activity(t:Trace): return tuple(e.activity for e in t.events)
def stutter(t:Trace):
    out=[]
    for x in activity(t):
        if not out or out[-1]!=x: out.append(x)
    return tuple(out)
def project(t,p):
    p=Profile(p)
    return exact(t) if p is Profile.EXACT else activity(t) if p is Profile.ACTIVITY else stutter(t)
