from datetime import datetime, timezone, timedelta
from scripts.measure_train.coherence.subject import Subject, Refusal
from scripts.measure_train.coherence.obligation import Axis
from scripts.measure_train.coherence.witness import Witness, Outcome
from scripts.measure_train.coherence.freshness import require_fresh
import unittest
S=Subject("seanchatmangpt/chatman-ecosystem","24b39444364cb959f92525453de69981ca511af3")
T=datetime(2026,8,22,9,0,tzinfo=timezone.utc)
class TestFreshness(unittest.TestCase):
 def test_stale_dropped_only_when_ttl_configured(self):
  old=Witness(S,Axis.FOCUSED,"repo",Outcome.PASS,T-timedelta(hours=3),"run")
  self.assertEqual(require_fresh([old],T,{}),(old,)); self.assertEqual(require_fresh([old],T,{"FOCUSED":timedelta(hours=2)}),())
 def test_future_refuses(self):
  future=Witness(S,Axis.FOCUSED,"repo",Outcome.PASS,T+timedelta(seconds=1),"run")
  with self.assertRaisesRegex(Refusal,"FUTURE_EVIDENCE"): require_fresh([future],T,{})
if __name__=="__main__": unittest.main()
