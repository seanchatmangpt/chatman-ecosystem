import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.fusion_realization_msa.subject import Subject
from scripts.measure_train.fusion_realization_msa.sensor import SensorIdentity
from scripts.measure_train.fusion_realization_msa.plan import FusionPlan
from scripts.measure_train.fusion_realization_msa.outcome import SensorOutcome
from scripts.measure_train.fusion_realization_msa.frontier import CalibrationFrontier
from scripts.measure_train.fusion_realization_msa.calibration import calibrate_gain
from scripts.measure_train.fusion_realization_msa.cusum import two_sided_cusum
from scripts.measure_train.fusion_realization_msa.qualify import qualify
from scripts.measure_train.fusion_realization_msa.replay import replay
class T(unittest.TestCase):
 def test_realized_fusion_caps_at_partial_alive(self):
  now=datetime.now(timezone.utc); subject=Subject("o/r","a"*40); front=CalibrationFrontier("fusion",3,"f"*64)
  sensors=(SensorIdentity("a","fa","ra","1"*64,"a"*64),SensorIdentity("b","fb","rb","2"*64,"b"*64))
  plan=FusionPlan(subject,"plan",front.digest,("a","b"),.5,5,100,now)
  outs=(SensorOutcome(subject,"plan","a","ea",(.55,.45),("1",),1,20,now+timedelta(seconds=1)),SensorOutcome(subject,"plan","b","eb",(.45,.55),("2",),1,30,now+timedelta(seconds=1)))
  cal=calibrate_gain(((.5,.5),)*5); drift=two_sided_cusum((0,0,0))
  weights={"a":.3,"b":.3}; value=lambda ss:sum(weights[x] for x in ss)
  q=qualify(plan,outs,sensors,front,cal,drift,((1,0),(0,1)),value,(("plan",.5),("alt",.4)))
  self.assertEqual(q["standing"],"PARTIAL_ALIVE"); self.assertFalse(q["actuation_performed"]); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
