import unittest
from fractions import Fraction
from scripts.release_train.process_evidence_crown import *
from scripts.release_train.process_evidence_crown.methodology import REQUIRED as METHODS
from scripts.release_train.process_evidence_crown.rails import REQUIRED as RAILS
from scripts.release_train.process_evidence_crown.failures import REQUIRED as FAILURES
class T(unittest.TestCase):
 def build(self,fail=False):
  s=Subject.parse('seanchatmangpt/chatman-ecosystem','3'*40,'4'*64)
  ns={}
  kinds=[EvidenceKind.SEMANTIC,EvidenceKind.TRACE,EvidenceKind.CALIBRATION,EvidenceKind.REALIZATION,EvidenceKind.METHODOLOGY,EvidenceKind.RUNTIME,EvidenceKind.SECURITY,EvidenceKind.ORACLE,EvidenceKind.REPLAY]
  for i,k in enumerate(kinds): ns[str(i)]=EvidenceNode(str(i),s,k,7,Interval(Fraction(9,10),Fraction(1)),Outcome.FAIL if fail and i==5 else Outcome.PASS,f'i{i}',f'm{i}',f'd{i}')
  parents={str(i):(str(i-1),) for i in range(1,len(ns))}
  return s,EvidenceGraph(ns,parents)
 def test_chicago_partial_alive_and_replay(self):
  s,g=self.build(False); q=qualify(s,7,g,METHODS,{x:'PASS' for x in RAILS},{x:'REFUSED' for x in FAILURES})
  self.assertEqual(q.standing.value,'PARTIAL_ALIVE'); self.assertIsNotNone(q.receipt); self.assertEqual(replay(q.receipt,q.receipt.digest),'REPLAY_MATCH')
 def test_red_dependency_dominates_and_suppresses_receipt(self):
  s,g=self.build(True); q=qualify(s,7,g,METHODS,{x:'PASS' for x in RAILS},{x:'PASS' for x in FAILURES})
  self.assertEqual(q.standing.value,'BUILD_BROKEN'); self.assertIsNone(q.receipt)
