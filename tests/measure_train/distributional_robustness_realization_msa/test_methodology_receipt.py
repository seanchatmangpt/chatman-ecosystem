import unittest
from fractions import Fraction
from scripts.measure_train.distributional_robustness_realization_msa.methodology import REQUIRED,require_complete
from scripts.measure_train.distributional_robustness_realization_msa.subject import Subject
from scripts.measure_train.distributional_robustness_realization_msa.ambiguity import AmbiguityModel
from scripts.measure_train.distributional_robustness_realization_msa.receipt import manufacture
from scripts.measure_train.distributional_robustness_realization_msa.replay import replay
from scripts.measure_train.distributional_robustness_realization_msa.refusal import Refused
class T(unittest.TestCase):
 def test_methodology_replay(self):
  self.assertTrue(require_complete(REQUIRED)["complete"]); s=Subject("o/r","a"*40,"b"*64,1); m=AmbiguityModel("TV",Fraction(1,10),1,"c"*64); r=manufacture(s,(m,),(),"PARTIAL_ALIVE"); self.assertEqual(replay(r),"REPLAY_MATCH"); r["body"]["standing"]="ALIVE"
  with self.assertRaisesRegex(Refused,"RECEIPT_MISMATCH"): replay(r)
