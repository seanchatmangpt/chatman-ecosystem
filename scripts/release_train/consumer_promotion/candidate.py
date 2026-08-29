from dataclasses import dataclass
@dataclass(frozen=True)
class Candidate:
    name:str
    dependency_relief:int
    reversibility:int
    admitted:bool
def select(candidates:list[Candidate])->Candidate:
    viable=[c for c in candidates if c.admitted]
    if not viable: raise ValueError("REFUSED[NO_VIABLE_CANDIDATE]")
    return sorted(viable,key=lambda c:(-c.dependency_relief,-c.reversibility,c.name))[0]
