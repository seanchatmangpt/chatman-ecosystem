from datetime import datetime, timezone
from copy import deepcopy
from scripts.measure_train.coherence.subject import Subject, Refusal
from scripts.measure_train.coherence.obligation import Axis, Obligation
from scripts.measure_train.coherence.witness import Witness, Outcome
from scripts.measure_train.coherence.coverage import cover
from scripts.measure_train.coherence.coherence import evaluate
from scripts.measure_train.coherence.receipt import manufacture
from scripts.measure_train.coherence.replay import verify
import unittest
S=Subject("seanchatmangpt/chatman-ecosystem","24b39444364cb959f92525453de69981ca511af3")
T=datetime(2026,8,22,9,0,tzinfo=timezone.utc)
class TestReceipt(unittest.TestCase):
 def test_deterministic_and_non_actuating(self):
  o=[Obligation("repo",Axis.REPOSITORY,"repo")]; w=[Witness(S,Axis.REPOSITORY,"repo",Outcome.PASS,T,"run")]; c=cover(o,w); h=evaluate(c)
  a=manufacture(S,h,c); b=manufacture(S,h,c); self.assertEqual(a,b); self.assertFalse(a["body"]["actuation_performed"])
 def test_tamper_refuses(self):
  o=[Obligation("repo",Axis.REPOSITORY,"repo")]; w=[Witness(S,Axis.REPOSITORY,"repo",Outcome.PASS,T,"run")]; c=cover(o,w); h=evaluate(c); r=deepcopy(manufacture(S,h,c)); r["body"]["standing"]="ALIVE"
  with self.assertRaisesRegex(Refusal,"RECEIPT_MISMATCH"): verify(r,S,h,c)
if __name__=="__main__": unittest.main()
