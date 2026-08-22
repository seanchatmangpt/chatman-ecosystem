from dataclasses import dataclass
class RolloutRefusal(ValueError): pass
@dataclass(frozen=True)
class Stage:
    name:str
    action:str
ALLOWED={"VERIFY","CONSTRUCT","SELECT"}
def build_rollout(component_order):
    stages=[]
    for c in component_order:
        stages.append(Stage(f"verify:{c}","VERIFY"))
        stages.append(Stage(f"construct:{c}","CONSTRUCT"))
    if any(s.action not in ALLOWED for s in stages): raise RolloutRefusal("REFUSED[CONSEQUENTIAL_ROLLOUT]")
    return tuple(stages)
