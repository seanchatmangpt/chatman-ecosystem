import unittest
from scripts.release_train.provenance_reconciliation.admission import admit_subject
from scripts.release_train.provenance_reconciliation.claims import EvidenceClaim
from scripts.release_train.provenance_reconciliation.model import Refused
from scripts.release_train.provenance_reconciliation.obligations import ObligationProfile
from tests.release_train.provenance_reconciliation.helpers import SUBJECT_A,records_for,claims_for

class AdmissionCourt(unittest.TestCase):
    def test_foreign_evidence_refused(self):
        claims=claims_for(SUBJECT_A); claims[0]=EvidenceClaim("bad",SUBJECT_A,"focused","ALIVE",("foreign",))
        with self.assertRaisesRegex(Refused,"CLAIM_REFERENCES_FOREIGN_EVIDENCE"): admit_subject(SUBJECT_A,records_for(SUBJECT_A),claims,ObligationProfile())
    def test_repository_alive_cannot_launder_failed_scope(self):
        claims=claims_for(SUBJECT_A); claims[0]=EvidenceClaim("bad",SUBJECT_A,"focused","BUILD_BROKEN",(f"{SUBJECT_A.repo}:focused",))
        with self.assertRaisesRegex(Refused,"REPOSITORY_ALIVE_LAUNDERS_FAILED_SCOPE"): admit_subject(SUBJECT_A,records_for(SUBJECT_A),claims,ObligationProfile())
if __name__ == "__main__": unittest.main()
