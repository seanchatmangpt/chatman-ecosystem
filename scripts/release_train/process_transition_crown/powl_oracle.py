from dataclasses import dataclass
from .refusal import Refused

@dataclass(frozen=True)
class PowlModel:
    starts: tuple[str,...]
    successors: dict[str,tuple[str,...]]
    max_steps: int

    def traces(self):
        if self.max_steps <= 0: raise Refused("INVALID_POWL_BOUND")
        out=set()
        def walk(path):
            node=path[-1]
            nxt=self.successors.get(node,())
            if not nxt or len(path)>=self.max_steps:
                out.add(tuple(path)); return
            for n in nxt: walk(path+(n,))
        for s in self.starts: walk((s,))
        return frozenset(out)

def require_correspondence(candidate:set[tuple[str,...]], reference:set[tuple[str,...]]):
    extra=set(candidate)-set(reference); missing=set(reference)-set(candidate)
    if extra: raise Refused("POWL_UNSOUND",repr(sorted(extra)))
    if missing: raise Refused("POWL_INCOMPLETE",repr(sorted(missing)))
    return True
