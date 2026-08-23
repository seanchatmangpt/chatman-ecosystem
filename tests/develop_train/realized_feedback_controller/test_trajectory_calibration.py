import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.develop_train.realized_feedback_controller.calibration import GainCalibration
from scripts.develop_train.realized_feedback_controller.realization import StepRealization
from scripts.develop_train.realized_feedback_controller.trajectory import Trajectory
class TestTrajectory(unittest.TestCase):
 def test_contiguous_calibration(self):
  t=datetime.now(timezone.utc); xs=tuple(StepRealization(i,str(i),Fraction(1,2),Fraction(2,5),1,1,1,t) for i in range(3)); c=GainCalibration.from_trajectory(Trajectory(xs)); self.assertEqual(c.bias,Fraction(-1,10)); self.assertTrue(c.admitted())
