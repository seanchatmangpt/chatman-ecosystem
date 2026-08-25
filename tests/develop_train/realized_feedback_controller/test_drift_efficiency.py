import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.develop_train.realized_feedback_controller.drift import from_residuals
from scripts.develop_train.realized_feedback_controller.efficiency import Efficiency
from scripts.develop_train.realized_feedback_controller.realization import StepRealization
from scripts.develop_train.realized_feedback_controller.trajectory import Trajectory
class TestDrift(unittest.TestCase):
 def test_drift_and_efficiency(self):
  self.assertTrue(from_residuals([Fraction(-1),Fraction(1),Fraction(1),Fraction(1)]).drifted())
  t=datetime.now(timezone.utc); tr=Trajectory(tuple(StepRealization(i,str(i),1,1,2,1,1,t) for i in range(3))); self.assertEqual(Efficiency.from_trajectory(tr).information_per_cost,Fraction(1,2))
