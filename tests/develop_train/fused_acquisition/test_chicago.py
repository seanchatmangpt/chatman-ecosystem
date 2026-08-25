import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.develop_train.fused_acquisition.subject import Subject
from scripts.develop_train.fused_acquisition.calibration import Calibration
from scripts.develop_train.fused_acquisition.sensor import Sensor,Observation
from scripts.develop_train.fused_acquisition.independence import IndependenceProof
from scripts.develop_train.fused_acquisition.currentness import frontier
from scripts.develop_train.fused_acquisition.acquisition import AcquisitionCandidate,Budget
from scripts.develop_train.fused_acquisition.engine import qualify
from scripts.develop_train.fused_acquisition.receipt import replay
class TestChicago(unittest.TestCase):
 def test_current_and_ambiguous_worlds(self):
  sub=Subject('seanchatmangpt/chatman-ecosystem','a'*40); now=datetime.now(timezone.utc)-timedelta(seconds=1)
  sensors=[Sensor('s1','f1','d1',Calibration(5,'1'*64,30,Fraction(1,20),Fraction(1,20),0)),Sensor('s2','f2','d2',Calibration(5,'2'*64,30,Fraction(1,20),Fraction(1,20),0))]
  proofs=[IndependenceProof('s1','s2','f'*64)]; fr=frontier(sensors)
  cands=[AcquisitionCandidate('probe3','s3',Fraction(4,5),Fraction(3,4),2,1)]
  q=qualify(sub,sensors,[Observation('s1',5,'CURRENT',1,now),Observation('s2',5,'CURRENT',1,now)],proofs,fr,cands,Budget(5,5),'MAX_INFORMATION')
  self.assertEqual((q.topology,q.standing,q.selected_candidate),('CURRENT','PARTIAL_ALIVE',None)); self.assertTrue(replay(q.receipt,q.receipt.digest())); self.assertFalse(q.receipt.actuation_performed)
  q2=qualify(sub,sensors,[Observation('s1',5,'CURRENT',1,now),Observation('s2',5,'STALE',1,now)],proofs,fr,cands,Budget(5,5),'MAX_INFORMATION')
  self.assertEqual((q2.topology,q2.standing,q2.selected_candidate),('AMBIGUOUS','UNKNOWN','probe3'))
