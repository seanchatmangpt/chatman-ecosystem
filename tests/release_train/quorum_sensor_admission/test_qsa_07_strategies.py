import unittest
from fractions import Fraction
from scripts.release_train.quorum_sensor_admission.strategy import Strategy, score_strategies, select
from scripts.release_train.quorum_sensor_admission.topology import Topology, TopologyResult
class StrategyCourt(unittest.TestCase):
 def test_strategies_remain_distinct(self):
  scores=score_strategies(TopologyResult(Topology.HEALTHY,0),Fraction(1),5); self.assertEqual({s.strategy for s in scores},{Strategy.STRICT_CURRENT,Strategy.MAX_COVERAGE,Strategy.MIN_AMBIGUITY}); self.assertIsNotNone(select(scores))
 def test_split_brain_admits_none(self): self.assertIsNone(select(score_strategies(TopologyResult(Topology.SPLIT_BRAIN,3),Fraction(1),5)))
if __name__=="__main__": unittest.main()
