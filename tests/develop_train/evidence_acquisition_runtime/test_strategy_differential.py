import unittest
from fractions import Fraction
from scripts.develop_train.evidence_acquisition_runtime.candidate import EvidenceCandidate
from scripts.develop_train.evidence_acquisition_runtime.strategies import CandidateScore,Strategy,rank
class T(unittest.TestCase):
 def test_strategies_remain_distinct(self):
  a=EvidenceCandidate('expensive','f1','d1','s',Fraction(10),1); b=EvidenceCandidate('efficient','f2','d2','s',Fraction(1),1); sc=[CandidateScore(a,.8,1,.2),CandidateScore(b,.3,1,.7)]
  self.assertEqual(rank(sc,Strategy.MAX_INFORMATION_GAIN)[0].candidate.candidate_id,'expensive'); self.assertEqual(rank(sc,Strategy.MAX_INFORMATION_PER_COST)[0].candidate.candidate_id,'efficient')
