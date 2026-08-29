import unittest
from scripts.release_train.provenance_reconciliation.claims import EvidenceClaim, repository_standing
from scripts.release_train.provenance_reconciliation.model import Refused
from tests.release_train.provenance_reconciliation.helpers import SUBJECT_A

class ClaimCourt(unittest.TestCase):
    def test_evidence_free_refused(self):
        with self.assertRaisesRegex(Refused,"EVIDENCE_FREE_CLAIM"): EvidenceClaim("c",SUBJECT_A,"focused","ALIVE",()).admit()
    def test_repository_conflict_refused(self):
        cs=[EvidenceClaim("a",SUBJECT_A,"repository","ALIVE",("x",)),EvidenceClaim("b",SUBJECT_A,"repository","BUILD_BROKEN",("y",))]
        with self.assertRaisesRegex(Refused,"CONTRADICTORY_REPOSITORY_STANDING"): repository_standing(cs,SUBJECT_A)
if __name__ == "__main__": unittest.main()
