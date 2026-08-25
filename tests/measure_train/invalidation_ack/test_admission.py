import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.invalidation_ack.subject import Subject,Refused
from scripts.measure_train.invalidation_ack.event import Invalidation
from scripts.measure_train.invalidation_ack.acknowledgement import Acknowledgement
from scripts.measure_train.invalidation_ack.admission import admit
class T(unittest.TestCase):
 def test_orphan_ack_refuses(self):
  now=datetime.now(timezone.utc); s=Subject("p/r","a"*40); c=Subject("c/r","b"*40)
  e=Invalidation(s,"e","BUILD_BROKEN",now)
  a=Acknowledgement("e",c,"missing",now+timedelta(seconds=1),"a")
  with self.assertRaises(Refused): admit(e,[],[a],[])
