import unittest
from scripts.release_train.provenance_reconciliation.model import Refused
from scripts.release_train.provenance_reconciliation.provenance import EvidenceRecord
from scripts.release_train.provenance_reconciliation.window import ObservationWindow
from tests.release_train.provenance_reconciliation.helpers import SUBJECT_A,DIGEST

W=ObservationWindow("2026-08-22T08:00:00Z","2026-08-22T10:00:00Z")
class ProvenanceCourt(unittest.TestCase):
    def test_ci_requires_run(self):
        with self.assertRaisesRegex(Refused,"MISSING_RUN_ID"): EvidenceRecord("e",SUBJECT_A,"ci_run","2026-08-22T09:00:00Z","https://github.com/a/b",DIGEST).admit(W)
    def test_artifact_requires_artifact_id(self):
        with self.assertRaisesRegex(Refused,"MISSING_ARTIFACT_ID"): EvidenceRecord("e",SUBJECT_A,"artifact","2026-08-22T09:00:00Z","https://github.com/a/b",DIGEST,run_id=1).admit(W)
    def test_non_github_refused(self):
        with self.assertRaisesRegex(Refused,"NON_GITHUB_EVIDENCE_SOURCE"): EvidenceRecord("e",SUBJECT_A,"receipt","2026-08-22T09:00:00Z","file:///tmp/x",DIGEST).admit(W)
if __name__ == "__main__": unittest.main()
