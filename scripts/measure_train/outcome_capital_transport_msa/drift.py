from dataclasses import dataclass
@dataclass
class Cusum:
    threshold: float
    slack: float=0.0
    value: float=0.0
    drifted: bool=False
    def update(self,residual):
        self.value=max(0.0,self.value+float(residual)-self.slack)
        if self.value>self.threshold: self.drifted=True
        return self.drifted
