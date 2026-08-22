import unittest
from scripts.develop_train.calibration_regime_quorum.independence import EvidenceSource,IndependenceProof,independent_cluster_count,relation
class IndependenceCourt(unittest.TestCase):
    def test_correlation_and_explicit_independence_remain_distinct(self):
        a=EvidenceSource("a","p1","r1","x1","family"); b=EvidenceSource("b","p2","r2","x2","family"); c=EvidenceSource("c","p3","r3","x3","other")
        self.assertEqual(relation(a,b),"CORRELATED"); self.assertEqual(relation(a,c),"UNKNOWN"); proof=IndependenceProof(a.fingerprint,c.fingerprint,True); self.assertEqual(relation(a,c,(proof,)),"INDEPENDENT"); self.assertEqual(independent_cluster_count((a,c),(proof,)),2)
    def test_unproven_independence_does_not_inflate_quorum(self):
        a=EvidenceSource("a","p1","r1","x1","f1"); b=EvidenceSource("b","p2","r2","x2","f2"); self.assertEqual(independent_cluster_count((a,b),()),1)
if __name__=="__main__": unittest.main()
