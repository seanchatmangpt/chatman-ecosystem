import unittest
from datetime import datetime, timezone, timedelta
from scripts.develop_train.process_transition_substrate import *
class T(unittest.TestCase):
 def test_current(self):
  e=SubjectEpoch("seanchatmangpt/chatman-ecosystem@"+"b"*40,2)
  ev=Evidence(e,Obligation("x",State.PASS,"ci"),datetime.now(timezone.utc),"c"*64)
  self.assertIs(admit(ev,e),ev)
  require_fresh(ev.observed_at,ev.observed_at+timedelta(seconds=1),2)
 def test_stale(self):
  now=datetime.now(timezone.utc)
  with self.assertRaises(Refused): require_fresh(now-timedelta(seconds=3),now,2)
