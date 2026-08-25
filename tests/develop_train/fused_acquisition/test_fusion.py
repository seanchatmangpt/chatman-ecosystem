import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.develop_train.fused_acquisition.calibration import Calibration
from scripts.develop_train.fused_acquisition.sensor import Sensor,Observation
from scripts.develop_train.fused_acquisition.fusion import robust_current_score
from scripts.develop_train.fused_acquisition.refusals import Refused
class TestFusion(unittest.TestCase):
 def test_robust_current_score_and_stale_binding(self):
  c1=Calibration(3,'1'*64,20,Fraction(1,20),Fraction(1,20),Fraction(0)); c2=Calibration(3,'2'*64,20,Fraction(0),Fraction(0),Fraction(0))
  xs=[Sensor('s1','f1','d1',c1),Sensor('s2','f2','d2',c2)]; now=datetime.now(timezone.utc)-timedelta(seconds=1)
  obs=[Observation('s1',3,'CURRENT',1,now),Observation('s2',3,'CURRENT',Fraction(4,5),now)]
  self.assertGreater(robust_current_score(xs,obs,{'s1','s2'}),Fraction(1,2))
  with self.assertRaises(Refused): robust_current_score(xs,[Observation('s1',2,'CURRENT',1,now),obs[1]],{'s1','s2'})
