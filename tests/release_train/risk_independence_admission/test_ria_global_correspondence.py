import sys,unittest
from datetime import datetime,timezone
sys.path.insert(0,'scripts/release_train')
from risk_independence_admission import Refused
from risk_independence_admission.methodology import REQUIRED,require_methodologies
from risk_independence_admission.correspondence import REQUIRED_RAILS,EngineEvidence,require_engines,require_rails
from risk_independence_admission.distribution import HostEvidence,require_distribution
from risk_independence_admission.failures import REQUIRED as FAILURES,require_failure_worlds
class GlobalCorrespondence(unittest.TestCase):
 def test_full_global_contract(self):
  d='a'*64; engines=[EngineEvidence('beam','1'*64,'3'*64,d),EngineEvidence('wasm','2'*64,'4'*64,d)]
  self.assertTrue(require_engines(engines)); self.assertTrue(require_rails({r:d for r in REQUIRED_RAILS})); self.assertTrue(require_methodologies(REQUIRED)); self.assertTrue(require_failure_worlds(FAILURES))
  now=datetime.now(timezone.utc); hs=[HostEvidence('h1','us',True,'c1',now),HostEvidence('h2','eu',True,'c2',now)]
  self.assertTrue(require_distribution(hs,now,60))
 def test_plaintext_refuses(self):
  now=datetime.now(timezone.utc)
  with self.assertRaises(Refused): require_distribution([HostEvidence('h1','us',False,'c',now),HostEvidence('h2','eu',True,'d',now)],now,60)
 def test_rail_divergence_refuses(self):
  d={r:'x' for r in REQUIRED_RAILS}; d['WASM']='y'
  with self.assertRaises(Refused): require_rails(d)
if __name__=='__main__':unittest.main()
