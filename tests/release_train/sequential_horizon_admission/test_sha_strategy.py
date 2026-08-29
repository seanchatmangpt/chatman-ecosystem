import unittest
from scripts.release_train.sequential_horizon_admission import Candidate,Strategy
from scripts.release_train.sequential_horizon_admission.strategy import select
class T(unittest.TestCase):
 def test_strategies_do_not_collapse(self):
  a=Candidate('a',10,1,10,8,0); b=Candidate('b',6,8,2,2,8)
  self.assertEqual(select([a,b],Strategy.MAX_INFORMATION).name,'a')
  self.assertEqual(select([a,b],Strategy.MAX_INDEPENDENCE).name,'b')
  self.assertEqual(select([a,b],Strategy.MINIMAX_LATENCY).name,'b')
