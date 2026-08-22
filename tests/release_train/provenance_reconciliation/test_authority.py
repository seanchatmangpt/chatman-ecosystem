import unittest
from scripts.release_train.provenance_reconciliation.authority import AuthorityContext
from scripts.release_train.provenance_reconciliation.model import Refused

class AuthorityCourt(unittest.TestCase):
    def test_select_construct_verify_allowed(self):
        a=AuthorityContext("schedule"); [a.admit(x) for x in ("SELECT","CONSTRUCT","VERIFY")]
    def test_do_refused_without_brce(self):
        with self.assertRaisesRegex(Refused,"BRCE_REQUIRED"): AuthorityContext("schedule").admit("DO")
    def test_live_cloud_refused_without_brce(self):
        with self.assertRaisesRegex(Refused,"BRCE_REQUIRED"): AuthorityContext("schedule").admit("LIVE_CLOUD")
if __name__ == "__main__": unittest.main()
