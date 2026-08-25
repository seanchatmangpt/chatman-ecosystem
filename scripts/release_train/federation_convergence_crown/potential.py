from dataclasses import dataclass
@dataclass(frozen=True)
class Potential:
    blockers:int; error_ppm:int; churn:int
    @property
    def lexicographic(self): return (self.blockers,self.error_ppm,self.churn)
def descending(a,b): return b.lexicographic<a.lexicographic
