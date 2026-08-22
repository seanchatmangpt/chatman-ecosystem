import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.develop_train.evidence_acquisition_runtime.subject import Subject,Refusal
from scripts.develop_train.evidence_acquisition_runtime.predictive import Belief
from scripts.develop_train.evidence_acquisition_runtime.candidate import EvidenceCandidate
from scripts.develop_train.evidence_acquisition_runtime.calibration import SensorCalibration
from scripts.develop_train.evidence_acquisition_runtime.independence import IndependenceProof
from scripts.develop_train.evidence_acquisition_runtime.budget import AcquisitionBudget
from scripts.develop_train.evidence_acquisition_runtime.strategies import Strategy
from scripts.develop_train.evidence_acquisition_runtime.frontier import CalibrationFrontier
from scripts.develop_train.evidence_acquisition_runtime.engine import qualify
class T(unittest.TestCase):
 def test_unresolved_state_selects_independent_evidence_then_stale_frontier_refuses(self):
  n=datetime(2026,8,22,22,tzinfo=timezone.utc); cs=[EvidenceCandidate('detector','regime','python','recovery',Fraction(2),30),EvidenceCandidate('rail','verification','ci','repo',Fraction(1),20),EvidenceCandidate('duplicate','verification','ci2','repo',Fraction(1),20)]
  cal=[SensorCalibration('detector',7,50,Fraction(9,10),Fraction(1,20),n),SensorCalibration('rail',7,50,Fraction(4,5),Fraction(1,10),n),SensorCalibration('duplicate',7,50,Fraction(4,5),Fraction(1,10),n)]; f=CalibrationFrontier.build(cal)
  ps=[IndependenceProof('detector','rail','a'*64),IndependenceProof('detector','duplicate','b'*64),IndependenceProof('rail','duplicate','c'*64)]
  args=dict(subject=Subject('seanchatmangpt/chatman-ecosystem','1'*40),belief=Belief(Fraction(2,5),9),candidates=cs,proofs=ps,budget=AcquisitionBudget(Fraction(3),60,2),strategy=Strategy.MAX_INFORMATION_PER_COST)
  q=qualify(**args,calibrations=cal,now=n,expected_frontier=f); self.assertEqual(len(q.selection.candidate_ids),2); self.assertIn('detector',q.selection.candidate_ids)
  moved=[SensorCalibration(x.candidate_id,8,x.support,x.true_positive_rate,x.false_positive_rate,n+timedelta(minutes=1)) for x in cal]
  with self.assertRaisesRegex(Refusal,'STALE_CALIBRATION_FRONTIER'): qualify(**args,calibrations=moved,now=n+timedelta(minutes=1),expected_frontier=f)
