import unittest
from fractions import Fraction
from scripts.release_train.quorum_sensor_admission import Relation, VectorClock, strict_majority
from scripts.release_train.quorum_sensor_admission.topology import Topology, classify
from common import SUBJECT, clocks, votes
class CausalityTopologyCourt(unittest.TestCase):
 def test_concurrency_preserved(self): self.assertEqual(VectorClock.from_dict({"a":1}).compare(VectorClock.from_dict({"b":1})),Relation.CONCURRENT)
 def test_healthy_vs_split_brain(self):
  q=strict_majority(SUBJECT,("r1","r2","r3"),votes()); self.assertEqual(classify(votes(),q,clocks(),Fraction(1)).topology,Topology.HEALTHY)
  mixed=votes()[:2]+[type(votes()[0])(SUBJECT,"r3",7,"d"*64)]; self.assertEqual(classify(mixed,None,clocks(True),Fraction(1)).topology,Topology.SPLIT_BRAIN)
if __name__=="__main__": unittest.main()
