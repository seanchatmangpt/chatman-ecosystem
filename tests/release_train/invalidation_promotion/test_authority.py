import unittest
from scripts.release_train.invalidation_promotion.authority import require_authority
from scripts.release_train.invalidation_promotion.subject import Refusal
class T(unittest.TestCase):
 def test_construct_allowed_and_release_refused(self):
  self.assertEqual(require_authority('CONSTRUCT'),'CONSTRUCT')
  with self.assertRaises(Refusal):
   require_authority('RELEASE')
