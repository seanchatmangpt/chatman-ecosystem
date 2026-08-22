import unittest
from fractions import Fraction
from scripts.develop_train.evidence_acquisition_runtime.candidate import EvidenceCandidate
from scripts.develop_train.evidence_acquisition_runtime.budget import AcquisitionBudget
from scripts.develop_train.evidence_acquisition_runtime.strategies import CandidateScore,Strategy
from scripts.develop_train.evidence_acquisition_runtime.selector import select
class T(unittest.TestCase):
 def test_budget_and_independence_bound_selection(self):
  a=EvidenceCandidate('a','f1','d1','s',Fraction(2),10); b=EvidenceCandidate('b','f2','d2','s',Fraction(2),10); c=EvidenceCandidate('c','f3','d3','s',Fraction(5),10)
  sc=[CandidateScore(a,.4,1,.6),CandidateScore(b,.3,1,.7),CandidateScore(c,.9,1,.1)]; pairs={frozenset(('a','b')),frozenset(('a','c')),frozenset(('b','c'))}
  self.assertEqual(set(select(sc,Strategy.MAX_INFORMATION_GAIN,AcquisitionBudget(Fraction(4),30,2),pairs).candidate_ids),{'a','b'})
