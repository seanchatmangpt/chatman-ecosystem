import unittest
from scripts.release_train.regime_current_recovery.engine import qualify
from scripts.release_train.regime_current_recovery.evidence import EvidenceSource
from scripts.release_train.regime_current_recovery.dependencies import DependencyGraph
from scripts.release_train.regime_current_recovery.persistence import PersistenceNeed
from scripts.release_train.regime_current_recovery.regime import RegimeState
from scripts.release_train.regime_current_recovery.subject import Refusal
from fixtures import SUBJECT,DEP,NOW,frontier,witness
class T(unittest.TestCase):
 def test_current_independent(self):
  f1,f2=frontier('s1'),frontier('s2'); a=EvidenceSource('p1','r1','a1','f1'); b=EvidenceSource('p2','r2','a2','f2'); pairs={frozenset((a.fingerprint,b.fingerprint))}; ws=[witness('s1',a,front=f1),witness('s2',b,front=f2)]; q=qualify(SUBJECT,ws,{'s1':f1,'s2':f2},DependencyGraph({SUBJECT:(DEP,)}),{DEP:'PARTIAL_ALIVE'},NOW,pairs,PersistenceNeed(transactional=True)); self.assertEqual(q.standing,'PARTIAL_ALIVE'); self.assertEqual(q.store,'SQLITE'); self.assertEqual(q.phases,('VERIFY','CONSTRUCT')); self.assertFalse(q.receipt.body['actuation_performed'])
 def test_stale(self):
  current=frontier('s1',generation=3); stale=frontier('s1',generation=2)
  with self.assertRaisesRegex(Refusal,'STALE_CALIBRATION_REGIME'): qualify(SUBJECT,[witness('s1',generation=2,front=stale)],{'s1':current},DependencyGraph({}),{},NOW)
 def test_drifted(self):
  drift=frontier('s1',state=RegimeState.DRIFT)
  with self.assertRaisesRegex(Refusal,'CALIBRATION_DRIFTED'): qualify(SUBJECT,[witness('s1',front=drift)],{'s1':drift},DependencyGraph({}),{},NOW)
