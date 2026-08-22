import unittest
from datetime import datetime,timezone
from scripts.measure_train.invalidation_ack.subject import Subject
from scripts.measure_train.invalidation_ack.event import Invalidation
from scripts.measure_train.invalidation_ack.telemetry import project
class T(unittest.TestCase):
 def test_exact_identity_and_state(self):
  p=Subject("p/r","a"*40); c=Subject("c/r","b"*40); e=Invalidation(p,"e","BUILD_BROKEN",datetime.now(timezone.utc))
  row=project(e,[(c,2,"PENDING_ACK")])[0]
  self.assertEqual((row["producer_sha"],row["consumer_sha"],row["cascade_depth"],row["state"]),(p.sha,c.sha,2,"PENDING_ACK"))
