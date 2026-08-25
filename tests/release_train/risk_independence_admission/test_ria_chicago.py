import sys,unittest
from datetime import datetime,timezone
from fractions import Fraction
sys.path.insert(0,'scripts/release_train')
from risk_independence_admission import *
from risk_independence_admission.methodology import REQUIRED
from risk_independence_admission.correspondence import REQUIRED_RAILS,EngineEvidence
from risk_independence_admission.distribution import HostEvidence
from risk_independence_admission.failures import REQUIRED as FAILURES
from risk_independence_admission.authority import ActionClass,admit
from risk_independence_admission.dependencies import DependencyGraph
class Chicago(unittest.TestCase):
 def world(self):
  d='f'*64; now=datetime.now(timezone.utc)
  return dict(subject=Subject('seanchatmangpt/chatman-ecosystem','b'*40),evidence=BetaEvidence(30,1),losses=LossMatrix(9,2,3),calibration=DecisionCalibration(3,'c'*64,40,'1/40','1/40','1/20'),frontier=CalibrationFrontier([DecisionCalibration(3,'c'*64,40,'1/40','1/40','1/20')]),ancestry_pair=(EvidenceAncestry((('left','r1'),('right','r2'))),'left','right'),pair_overlap=Fraction(1,20),higher_overlap=Fraction(1,20),max_pair=Fraction(1,5),max_higher=Fraction(1,5),candidate_intervals=(Interval('3/5','4/5'),Interval('2/3','9/10')),methodologies=REQUIRED,engines=[EngineEvidence('beam','1'*64,'3'*64,d),EngineEvidence('wasm','2'*64,'4'*64,d)],rails={r:d for r in REQUIRED_RAILS},hosts=[HostEvidence('h1','us',True,'c1',now),HostEvidence('h2','eu',True,'c2',now)],now=now,max_age_seconds=60,failure_worlds=FAILURES)
 def test_chicago_qualified_is_bounded_and_replayable(self):
  q=qualify(**self.world()); self.assertEqual(q.standing,Standing.PARTIAL_ALIVE); self.assertTrue(replay(q.receipt)); self.assertFalse(q.receipt.actuation_performed)
 def test_dependency_failure_suppresses_receipt(self):
  w=self.world();w['failed']=True;q=qualify(**w);self.assertEqual(q.standing,Standing.BUILD_BROKEN);self.assertIsNone(q.receipt)
 def test_transitive_dependency_blocker_suppresses_receipt(self):
  w=self.world();w['dependency_graph']=DependencyGraph((('release','engine'),('engine','runtime')),broken={'runtime'});w['dependency_node']='release';q=qualify(**w);self.assertEqual(q.standing,Standing.BLOCKED);self.assertIsNone(q.receipt)
 def test_do_refuses(self):
  with self.assertRaises(Refused): admit(ActionClass.DO)
 def test_receipt_tamper_refuses(self):
  from dataclasses import replace
  q=qualify(**self.world()); bad=replace(q.receipt,standing='ALIVE')
  with self.assertRaises(Refused): replay(bad)
if __name__=='__main__':unittest.main()
