import unittest
from scripts.release_train.promotion_admission.authority import *
class T(unittest.TestCase):
    def test_brce_fence(self):
        for x in ("OBSERVE","SELECT","CONSTRUCT","VERIFY"): self.assertEqual(admit_action(x),x)
        for x in ("DO","MERGE","RELEASE","DEPLOY","CLOUD_ACTUATE"):
            with self.assertRaisesRegex(AuthorityRefusal,"BRCE_REQUIRED"): admit_action(x)
if __name__=="__main__": unittest.main()
