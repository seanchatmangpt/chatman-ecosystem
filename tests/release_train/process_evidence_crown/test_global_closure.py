import unittest
from datetime import datetime,timezone,timedelta
from scripts.release_train.process_evidence_crown import *
from scripts.release_train.process_evidence_crown.methodology import REQUIRED as METHODS
from scripts.release_train.process_evidence_crown.rails import REQUIRED as RAILS
from scripts.release_train.process_evidence_crown.failures import REQUIRED as FAILURES
class T(unittest.TestCase):
 def test_multi_engine_and_tls(self):
  e1=EngineWitness('BEAM','beam','a'*64,'t'*64,'s'); e2=EngineWitness('WASM','wasm','b'*64,'t'*64,'s'); self.assertTrue(require_multi_engine([e1,e2]))
  now=datetime.now(timezone.utc); h1=HostObservation('h1','r1',3,True,'c1',now); h2=HostObservation('h2','r2',3,True,'c2',now-timedelta(minutes=1)); self.assertTrue(require_distributed([h1,h2],3,now))
 def test_reactor_and_complete_sets(self):
  rc=ReactorCorrespondence('a'*64,'b'*64,'c'*64,'d'*64,'e'*64,True); self.assertTrue(rc.admit())
  from scripts.release_train.process_evidence_crown.methodology import require_methodologies
  from scripts.release_train.process_evidence_crown.rails import require_rails
  from scripts.release_train.process_evidence_crown.failures import require_failure_worlds
  self.assertTrue(require_methodologies(METHODS)); self.assertTrue(require_rails({x:'PASS' for x in RAILS})); self.assertTrue(require_failure_worlds({x:'REFUSED' for x in FAILURES}))
