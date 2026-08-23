import unittest
from fractions import Fraction
from scripts.release_train.quorum_sensor_admission import Refused, ReplicaVote, strict_majority
from common import SUBJECT, visibility, votes
class VisibilityQuorumCourt(unittest.TestCase):
 def test_exact_coverage_and_majority(self):
  v=visibility(("r1","r2")); self.assertEqual(v.coverage,Fraction(2,3)); self.assertEqual(strict_majority(SUBJECT,v.known_replicas,votes()[:2]).required,2)
 def test_duplicate_vote_cannot_inflate(self):
  duplicate=votes()[:2]+[ReplicaVote(SUBJECT,"r2",7,"c"*64)]
  with self.assertRaises(Refused): strict_majority(SUBJECT,("r1","r2","r3"),duplicate)
if __name__=="__main__": unittest.main()
