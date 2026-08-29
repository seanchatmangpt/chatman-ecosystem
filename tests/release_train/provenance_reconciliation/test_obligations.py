import unittest
from scripts.release_train.provenance_reconciliation.model import Refused
from scripts.release_train.provenance_reconciliation.obligations import ObligationProfile
from tests.release_train.provenance_reconciliation.helpers import SUBJECT_A,claims_for

class ObligationCourt(unittest.TestCase):
    def test_complete_profile_admitted(self): self.assertEqual(6,len(ObligationProfile().require(SUBJECT_A,claims_for(SUBJECT_A))))
    def test_missing_scope_refused(self):
        with self.assertRaisesRegex(Refused,"INCOMPLETE_RELEASE_OBLIGATIONS"): ObligationProfile().require(SUBJECT_A,claims_for(SUBJECT_A)[:-1])
if __name__ == "__main__": unittest.main()
