import unittest
from scripts.release_train.promotion_epoch.subject import Subject
from scripts.release_train.promotion_epoch.candidate import PromotionCandidate
from scripts.release_train.promotion_epoch.barrier import REQUIRED
from scripts.release_train.promotion_epoch.risk import RiskVector
from scripts.release_train.promotion_epoch.engine import CandidateEvidence,manufacture_epoch
def gates(): return {x:"PASS" for x in REQUIRED}
class T(unittest.TestCase):
 def test_dependency_closed_epoch(self):
  a=PromotionCandidate("a",Subject("o/a","1"*40),Subject("o/a","2"*40),5,True,"ALIVE")
  b=PromotionCandidate("b",Subject("o/b","3"*40),Subject("o/b","4"*40),5,True,"ALIVE")
  ev={"a":CandidateEvidence(True,True,True,gates(),RiskVector(1,5,5,5)),"b":CandidateEvidence(True,True,True,gates(),RiskVector(2,5,5,5))}
  out=manufacture_epoch("a"*40,"b"*40,(a,b),ev,(("b","a"),))
  self.assertEqual(out["order"],("a","b")); self.assertFalse(out["actuation_performed"]); self.assertEqual(out["receipt"].barrier,"ALIVE")
 def test_unqualified_blocked(self):
  c=PromotionCandidate("c",Subject("o/c","1"*40),Subject("o/c","2"*40),5,True,"ALIVE")
  bad=gates(); bad["e2e"]="FAIL"
  with self.assertRaisesRegex(ValueError,"NO_QUALIFIED_PROMOTION"):
   manufacture_epoch("a"*40,"b"*40,(c,),{"c":CandidateEvidence(True,True,True,bad,RiskVector(1,5,5,5))})
