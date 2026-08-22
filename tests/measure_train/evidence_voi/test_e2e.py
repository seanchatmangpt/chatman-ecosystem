import unittest
from fractions import Fraction
from datetime import datetime,timezone
from scripts.measure_train.evidence_voi.subject import Subject,Refused
from scripts.measure_train.evidence_voi.belief import BeliefState
from scripts.measure_train.evidence_voi.candidate import MeasurementCandidate
from scripts.measure_train.evidence_voi.calibration import SensorCalibration
from scripts.measure_train.evidence_voi.budget import AcquisitionBudget
from scripts.measure_train.evidence_voi.dependence import IndependenceProof
from scripts.measure_train.evidence_voi.frontier import frontier_digest
from scripts.measure_train.evidence_voi.qualify import qualify
from scripts.measure_train.evidence_voi.receipt import replay
class T(unittest.TestCase):
 def test_chicago_select_only_and_stale_frontier(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40); b=BeliefState(Fraction(1,2),7)
  a=MeasurementCandidate("repo-ci","ci","github","REPOSITORY",Fraction(2),100)
  c=MeasurementCandidate("runtime","world","runner","RUNTIME",Fraction(1),50)
  ca=SensorCalibration("repo-ci",3,20,Fraction(9,10),Fraction(1,10),now)
  cc=SensorCalibration("runtime",4,20,Fraction(4,5),Fraction(1,5),now)
  proof=IndependenceProof("repo-ci","runtime","separate producer and implementation domain")
  digest=frontier_digest([a,c],[ca,cc])
  q=qualify(s,b,[a,c],[ca,cc],AcquisitionBudget(Fraction(3),100,2),now,[proof],expected_frontier=digest)
  self.assertEqual(q["standing"],"PARTIAL_ALIVE"); self.assertFalse(q["actuation_performed"]); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
  moved=SensorCalibration("runtime",5,20,Fraction(3,4),Fraction(1,4),now)
  with self.assertRaises(Refused): qualify(s,b,[a,c],[ca,moved],AcquisitionBudget(Fraction(3),100,2),now,[proof],expected_frontier=digest)
