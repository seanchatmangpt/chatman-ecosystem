import unittest
from fractions import Fraction
from scripts.measure_train.process_intelligence_convergence_msa.subject import Subject,Refused
from scripts.measure_train.process_intelligence_convergence_msa.convergence import ConvergenceResult
from scripts.measure_train.process_intelligence_convergence_msa.receipt import manufacture
from scripts.measure_train.process_intelligence_convergence_msa.replay import replay
class T(unittest.TestCase):
 def test_tamper_refuses(self):
  c=ConvergenceResult("CONVERGING",Fraction(1),Fraction(0),Fraction(-1),(),Fraction(1),Fraction(0))
  r=manufacture(Subject("o/r","a"*40,1),c,(),"PARTIAL_ALIVE")
  self.assertEqual(replay(r),"REPLAY_MATCH")
  r["body"]["standing"]="ALIVE"
  with self.assertRaises(Refused): replay(r)
