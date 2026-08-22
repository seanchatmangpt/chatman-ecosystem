from dataclasses import dataclass
@dataclass(frozen=True)
class Movement:
    head_moved:bool; pr_updated:bool; ci_changed:bool; dependency_changed:bool
    @property
    def material(self): return any((self.head_moved,self.pr_updated,self.ci_changed,self.dependency_changed))
    @property
    def dimensions(self): return tuple(k for k,v in (("head",self.head_moved),("pr",self.pr_updated),("ci",self.ci_changed),("dependency",self.dependency_changed)) if v)
