import unittest
from scripts.release_train.promotion_epoch.authority import admit,AuthorityRefusal
class T(unittest.TestCase):
 def test_construct(self): self.assertEqual(admit("CONSTRUCT"),"CONSTRUCT")
 def test_do_refuses(self):
  with self.assertRaises(AuthorityRefusal): admit("DO")
