from datetime import datetime, timezone, timedelta
import unittest
from scripts.develop_train.decision_outcome_evidence_capital import *

class IdentityProvenance(unittest.TestCase):
    def test_exact_subject_and_ancestry(self):
        with self.assertRaises(Refused):
            Subject.parse("x/y@abc")
        a=EvidenceNode("a",(), "impl-a","model-a","domain-a")
        b=EvidenceNode("b",(), "impl-b","model-b","domain-b")
        g=EvidenceGraph([a,b])
        self.assertTrue(require_distinct_provenance(a,b,g))

    def test_shared_root_refuses(self):
        r=EvidenceNode("r",(), "root","rootm","rootd")
        a=EvidenceNode("a",("r",), "a","am","ad")
        b=EvidenceNode("b",("r",), "b","bm","bd")
        g=EvidenceGraph([r,a,b])
        with self.assertRaises(Refused):
            require_distinct_provenance(a,b,g)

if __name__=="__main__": unittest.main()
