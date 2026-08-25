import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.fusion_realization_msa.subject import Subject,Refused
from scripts.measure_train.fusion_realization_msa.sensor import SensorIdentity
from scripts.measure_train.fusion_realization_msa.plan import FusionPlan
from scripts.measure_train.fusion_realization_msa.outcome import SensorOutcome
from scripts.measure_train.fusion_realization_msa.frontier import CalibrationFrontier
from scripts.measure_train.fusion_realization_msa.calibration import calibrate_gain
from scripts.measure_train.fusion_realization_msa.cusum import two_sided_cusum
from scripts.measure_train.fusion_realization_msa.admission import admit_realization
class T(unittest.TestCase):
 def test_stale_frontier_refuses(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40); sensor=SensorIdentity("x","f","r","1"*64,"2"*64)
  plan=FusionPlan(s,"p","3"*64,("x",),.1,1,10,now); out=SensorOutcome(s,"p","x","e",(.5,.5),("c",),0,1,now+timedelta(seconds=1))
  with self.assertRaises(Refused): admit_realization(plan,[out],[sensor],CalibrationFrontier("p",1,"4"*64),calibrate_gain(((.1,.1),)*5),two_sided_cusum((0,)))
