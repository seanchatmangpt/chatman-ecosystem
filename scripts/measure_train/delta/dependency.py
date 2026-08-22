from dataclasses import dataclass
@dataclass(frozen=True)
class DependencyDelta:
    component:str; before_sha:str; after_sha:str; ancestry:str
    def classify(self):
        if self.before_sha==self.after_sha: return "UNCHANGED"
        if self.ancestry=="DESCENDANT": return "FORWARD"
        if self.ancestry=="ANCESTOR": return "ROLLBACK"
        if self.ancestry=="DIVERGED": return "DIVERGED"
        return "UNKNOWN"
