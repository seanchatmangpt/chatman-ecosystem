import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.cross_control_msa.subject import Subject
from scripts.measure_train.cross_control_msa.identity import ControlIdentity
from scripts.measure_train.cross_control_msa.observation import Observation
from scripts.measure_train.cross_control_msa.admission import admit
from scripts.measure_train.cross_control_msa.refusal import Refused
class T(unittest.TestCase):
 def test_future_refuses(self):
  now=datetime.now(timezone.utc);s=Subject("o/r","a"*40,"b"*64,1);c=ControlIdentity("SEARCH","i","c"*64,"d"*64)
  with self.assertRaises(Refused): admit(s,[Observation(s,c,"x","e"*64,now+timedelta(seconds=1),"PASS")],now)
