import unittest
from scripts.measure_train.requalification_epoch.cross_repo import normalize_observation,reconcile_observations
class T(unittest.TestCase):
 def test_mixed_states_preserved(self):
  a=normalize_observation("o/r","a"*40,2,"e","PASS","focused"); b=normalize_observation("o/r","a"*40,2,"e","FAIL","repository")
  row=reconcile_observations([a,b])[0]; self.assertEqual(row[-1],("FAIL","PASS"))
