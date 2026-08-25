import unittest
from fractions import Fraction
from scripts.develop_train.fused_acquisition.acquisition import AcquisitionCandidate,Budget,select
class TestAcquisition(unittest.TestCase):
 def test_strategies_remain_distinct(self):
  a=AcquisitionCandidate('info','s3',Fraction(9,10),Fraction(1,10),10,5); b=AcquisitionCandidate('ind','s4',Fraction(1,2),Fraction(9,10),4,2); c=AcquisitionCandidate('cheap','s5',Fraction(1,3),Fraction(1,3),1,8)
  budget=Budget(20,20)
  self.assertEqual(select([a,b,c],budget,'MAX_INFORMATION').candidate_id,'info')
  self.assertEqual(select([a,b,c],budget,'MAX_INDEPENDENCE').candidate_id,'ind')
  self.assertEqual(select([a,b,c],budget,'MIN_COST').candidate_id,'cheap')
  self.assertEqual(select([a,b,c],budget,'MINIMAX_LATENCY').candidate_id,'ind')
