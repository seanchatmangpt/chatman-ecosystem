import unittest
from scripts.release_train.promotion_recovery.frontier import *
class T(unittest.TestCase):
 def test_strategies_remain_distinct(self):
  f=CandidateFrontier([CutCandidate('new',3,5,5),CutCandidate('fresh',2,10,3),CutCandidate('low-skew',1,3,0)])
  self.assertEqual(f.select('LATEST_COMPLETE').cut_id,'new')
  self.assertEqual(f.select('MAX_FRESHNESS').cut_id,'fresh')
  self.assertEqual(f.select('MIN_SKEW').cut_id,'low-skew')
