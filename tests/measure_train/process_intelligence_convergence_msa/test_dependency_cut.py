import unittest
from datetime import datetime,timezone
from scripts.measure_train.process_intelligence_convergence_msa.subject import Subject
from scripts.measure_train.process_intelligence_convergence_msa.obligation import ObligationState
from scripts.measure_train.process_intelligence_convergence_msa.epoch import ClosureEpoch
from scripts.measure_train.process_intelligence_convergence_msa.dependency import graph
from scripts.measure_train.process_intelligence_convergence_msa.cut import blocking_cut
class T(unittest.TestCase):
 def test_red_parent_is_cut(self):
  e=ClosureEpoch(Subject("o/r","a"*40,1),datetime.now(timezone.utc),(ObligationState("a","FAIL"),ObligationState("b","PASS")))
  self.assertEqual(blocking_cut(e,graph(["a","b"],[("b","a")])),("a",))
