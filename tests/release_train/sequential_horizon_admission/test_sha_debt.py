import unittest
from scripts.release_train.sequential_horizon_admission import DebtLedger,StepRealization
class T(unittest.TestCase):
 def test_realization_accumulates_information_and_resource_debt(self):
  d=DebtLedger().advance(StepRealization(1,2,1,4,6),planned_cost=3,planned_latency=4)
  self.assertEqual((d.information,d.cost_slip,d.latency_slip),(1,1,2))
