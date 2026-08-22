import unittest
from scripts.release_train.provenance_reconciliation.lineage import EvidenceEdge, order_evidence
from scripts.release_train.provenance_reconciliation.model import Refused
from tests.release_train.provenance_reconciliation.helpers import records_for,SUBJECT_A

class LineageCourt(unittest.TestCase):
    def test_cycle_refused(self):
        r=records_for(SUBJECT_A)[:2]
        with self.assertRaisesRegex(Refused,"EVIDENCE_LINEAGE_CYCLE"): order_evidence(r,[EvidenceEdge(r[0].evidence_id,r[1].evidence_id),EvidenceEdge(r[1].evidence_id,r[0].evidence_id)])
    def test_external_edge_refused(self):
        r=records_for(SUBJECT_A)[:1]
        with self.assertRaisesRegex(Refused,"EVIDENCE_EDGE_OUTSIDE_CLOSURE"): order_evidence(r,[EvidenceEdge(r[0].evidence_id,"missing")])
if __name__ == "__main__": unittest.main()
