import unittest
from scripts.release_train.regime_current_recovery.evidence import EvidenceSource
from scripts.release_train.regime_current_recovery.independence import relation,Relation,clusters
from scripts.release_train.regime_current_recovery.information import contribution,sequential_decision
from fixtures import model,witness
class T(unittest.TestCase):
 def test_correlation(self):
  a=EvidenceSource('p','r1','a1','family'); b=EvidenceSource('q','r2','a2','family'); self.assertEqual(relation(a,b),Relation.CORRELATED); self.assertEqual(len(clusters([witness('s1',a),witness('s1',b)])),1)
 def test_independent_zero(self):
  a=EvidenceSource('p','r1','a1','f1'); b=EvidenceSource('q','r2','a2','f2'); pairs={frozenset((a.fingerprint,b.fingerprint))}; self.assertEqual(relation(a,b,pairs),Relation.INDEPENDENT); self.assertEqual(contribution(model(),'UNKNOWN').value,0.0)
 def test_decision(self):
  decision,stat=sequential_decision([contribution(model(),'PASS'),contribution(model(),'PASS')],accept=1.0); self.assertEqual(decision,'ACCEPT_BOUNDED'); self.assertGreater(stat,1)
