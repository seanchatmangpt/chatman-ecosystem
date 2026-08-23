from dataclasses import dataclass
@dataclass
class Cusum:
    threshold:float; slack:float=0.0; score:float=0.0
    def update(self,value,reference):
        self.score=max(0.0,self.score+float(value-reference)-self.slack)
        return self.score>=self.threshold
