import unittest
from scripts.measure_train.federation_convergence_realization_msa.methodology import require_all,REQUIRED
from scripts.measure_train.federation_convergence_realization_msa.refusals import Refused
class T(unittest.TestCase):
 def test_complete(self):
  self.assertEqual(len(require_all(REQUIRED)),11)
  with self.assertRaises(Refused): require_all({'DISCOVERY'})
