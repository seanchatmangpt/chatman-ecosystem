from dataclasses import dataclass
ALLOWED={"PASS","FAIL","PENDING","UNKNOWN","UNSUPPORTED"}
@dataclass(frozen=True)
class CIVector:
    entries:tuple[tuple[str,str],...]
    @classmethod
    def from_mapping(cls,m):
        rows=[]
        for k,v in sorted(m.items()):
            if v not in ALLOWED: raise ValueError("REFUSED[INVALID_CI_OUTCOME]")
            rows.append((k,v))
        return cls(tuple(rows))
    def transition(self,other):
        a=dict(self.entries); b=dict(other.entries)
        return tuple((k,a.get(k,"UNKNOWN"),b.get(k,"UNKNOWN")) for k in sorted(set(a)|set(b)) if a.get(k,"UNKNOWN")!=b.get(k,"UNKNOWN"))
