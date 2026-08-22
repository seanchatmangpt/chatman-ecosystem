from dataclasses import dataclass,field
from .strategy import FrontierItem
@dataclass(slots=True)
class AckFrontier:
 expected:dict[str,bool]; discharged:set[str]=field(default_factory=set); seen_receipts:set[str]=field(default_factory=set)
 @classmethod
 def from_consumers(cls,consumers):return cls({s.identity:c for s,c in consumers})
 def record(self,subject,receipt):
  if subject.identity not in self.expected: raise ValueError('REFUSED[UNEXPECTED_CONSUMER]')
  if receipt in self.seen_receipts:return False
  self.seen_receipts.add(receipt);self.discharged.add(subject.identity);return True
 def items(self):return [FrontierItem(k,k in self.discharged,v) for k,v in sorted(self.expected.items())]
