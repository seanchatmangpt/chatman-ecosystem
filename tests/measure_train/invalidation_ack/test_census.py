import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.invalidation_ack.subject import Subject
from scripts.measure_train.invalidation_ack.event import Invalidation
from scripts.measure_train.invalidation_ack.delivery import Delivery
from scripts.measure_train.invalidation_ack.census import acknowledgement_census
class T(unittest.TestCase):
 def test_missing_ack_is_pending(self):
  now=datetime.now(timezone.utc); p=Subject("p/r","a"*40); c=Subject("c/r","b"*40); e=Invalidation(p,"e","BUILD_BROKEN",now)
  d=Delivery("e",c,now+timedelta(seconds=1),"d")
  self.assertEqual(acknowledgement_census(e,[(c,1)],[d],[],[])[0][2],"PENDING_ACK")
