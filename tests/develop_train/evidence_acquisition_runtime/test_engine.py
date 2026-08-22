import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.develop_train.evidence_acquisition_runtime.subject import Subject
from scripts.develop_train.evidence_acquisition_runtime.predictive import Belief
from scripts.develop_train.evidence_acquisition_runtime.candidate import EvidenceCandidate
from scripts.develop_train.evidence_acquisition_runtime.calibration import SensorCalibration
from scripts.develop_train.evidence_acquisition_runtime.independence import IndependenceProof
from scripts.develop_train.evidence_acquisition_runtime.budget import AcquisitionBudget
from scripts.develop_train.evidence_acquisition_runtime.strategies import Strategy
from scripts.develop_train.evidence_acquisition_runtime.engine import qualify
from scripts.develop_train.evidence_acquisition_runtime.receipt import replay
class T(unittest.TestCase):
 def test_dependency_closed_plan(self):
  n=datetime(2026,8,22,22,tzinfo=timezone.utc); cs=[EvidenceCandidate('a','pytest','linux','runtime',Fraction(1),10),EvidenceCandidate('b','gall','rust','format',Fraction(1),10)]; cal=[SensorCalibration('a',4,30,Fraction(9,10),Fraction(1,10),n),SensorCalibration('b',4,30,Fraction(4,5),Fraction(1,10),n)]
  q=qualify(subject=Subject('o/r','d'*40),belief=Belief(Fraction(1,3),2),candidates=cs,calibrations=cal,proofs=[IndependenceProof('a','b','e'*64)],budget=AcquisitionBudget(Fraction(3),100,2),strategy=Strategy.MAX_INFORMATION_GAIN,now=n)
  self.assertEqual(set(q.selection.candidate_ids),{'a','b'}); self.assertEqual(q.standing.value,'PARTIAL_ALIVE'); self.assertTrue(replay(q.receipt,q.receipt.digest())); self.assertFalse(q.receipt.actuation_performed)
