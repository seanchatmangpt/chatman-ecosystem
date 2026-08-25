import unittest
from datetime import datetime,timezone
from scripts.measure_train.strategy_binding.subject import Subject,Refused
from scripts.measure_train.strategy_binding.cut import CutCandidate
from scripts.measure_train.strategy_binding.policy import StrategyPolicy
from scripts.measure_train.strategy_binding.frontier import canonical_frontier
from scripts.measure_train.strategy_binding.proof import SelectionProof
from scripts.measure_train.strategy_binding.admission import admit
class T(unittest.TestCase):
 def test_policy_drift_refuses(self):
  n=datetime.now(timezone.utc); c=CutCandidate("c",1,(("o/a",1),),n); f,d=canonical_frontier([c]); old=StrategyPolicy("LATEST_COMPLETE"); new=StrategyPolicy("MAX_FRESHNESS")
  p=SelectionProof(Subject("c/r","a"*40),"c",old.digest,d,"p")
  with self.assertRaises(Refused): admit(p,new,f,d)
