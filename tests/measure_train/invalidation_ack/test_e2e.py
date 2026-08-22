import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.invalidation_ack.subject import Subject
from scripts.measure_train.invalidation_ack.event import Invalidation
from scripts.measure_train.invalidation_ack.delivery import Delivery
from scripts.measure_train.invalidation_ack.acknowledgement import Acknowledgement
from scripts.measure_train.invalidation_ack.discharge import Discharge
from scripts.measure_train.invalidation_ack.qualify import qualify
from scripts.measure_train.invalidation_ack.replay import replay
class T(unittest.TestCase):
 def test_all_consumers_must_discharge(self):
  now=datetime.now(timezone.utc); p=Subject("p/r","a"*40); c1=Subject("c/one","b"*40); c2=Subject("c/two","c"*40)
  e=Invalidation(p,"e","RECOVERED",now)
  d1=Delivery("e",c1,now+timedelta(seconds=1),"d1"); d2=Delivery("e",c2,now+timedelta(seconds=1),"d2")
  a1=Acknowledgement("e",c1,"d1",now+timedelta(seconds=2),"a1")
  x1=Discharge("e",c1,"a1","REQUALIFIED",now+timedelta(seconds=3),"proof1")
  q=qualify(e,[(p,c1),(p,c2)],[d1,d2],[a1],[x1])
  self.assertEqual(q["standing"],"UNKNOWN")
  self.assertFalse(q["actuation_performed"]); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
