from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True)
class VectorClock:
    entries: tuple
    @classmethod
    def from_dict(cls,d):
        if not d or any(not k or not isinstance(v,int) or v<0 for k,v in d.items()): raise Refused("REFUSED[INVALID_VECTOR_CLOCK]")
        return cls(tuple(sorted(d.items())))
    def as_dict(self): return dict(self.entries)
    def compare(self,other):
        a,b=self.as_dict(),other.as_dict(); keys=set(a)|set(b)
        le=all(a.get(k,0)<=b.get(k,0) for k in keys); ge=all(a.get(k,0)>=b.get(k,0) for k in keys)
        if le and ge:return "EQUAL"
        if le:return "BEFORE"
        if ge:return "AFTER"
        return "CONCURRENT"
    def join(self,other):
        a,b=self.as_dict(),other.as_dict(); return VectorClock.from_dict({k:max(a.get(k,0),b.get(k,0)) for k in set(a)|set(b)})
