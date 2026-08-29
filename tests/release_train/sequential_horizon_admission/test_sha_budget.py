import unittest
from fractions import Fraction
from scripts.release_train.sequential_horizon_admission import Budget,Refused
class T(unittest.TestCase):
 def test_budget_depletes_and_refuses_escape(self):
  b=Budget(Fraction(5),Fraction(10),2).consume(cost=2,latency=3)
  self.assertEqual((b.cost,b.latency,b.samples),(3,7,1))
  with self.assertRaises(Refused): b.consume(cost=4,latency=1)
