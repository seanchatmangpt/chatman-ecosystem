import unittest
from datetime import datetime,timezone
from scripts.measure_train.fusion_realization_msa.subject import Subject,Refused
from scripts.measure_train.fusion_realization_msa.plan import FusionPlan
from scripts.measure_train.fusion_realization_msa.outcome import SensorOutcome
from scripts.measure_train.fusion_realization_msa.budget import realize_budget
from scripts.measure_train.fusion_realization_msa.regret import observed_regret
class T(unittest.TestCase):
 def test_budget_and_observed_regret(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40); p=FusionPlan(s,"p","1"*64,("x",),.1,1,10,now)
  o=SensorOutcome(s,"p","x","e",(.5,.5),(),2,20,now)
  self.assertFalse(realize_budget(p,[o]).within_budget)
  self.assertEqual(observed_regret("p",(("p",1.0),("q",1.5))),.5)
  with self.assertRaises(Refused): observed_regret("z",(("p",1.0),))
