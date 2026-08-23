import unittest
from fractions import Fraction
from scripts.release_train.sequential_horizon_admission import *
class T(unittest.TestCase):
 def base(self):
  sid=Subject('seanchatmangpt/chatman-ecosystem@'+'a'*40); ident=ControllerIdentity(4,'b'*64,7,'c'*64)
  return sid,ident,HorizonPolicy(3,Fraction(9,10),2,2,2),Budget(10,10,3),GainCalibration(8,Fraction(1,10),Fraction(9,10),0,1),DebtLedger(),[Candidate('probe',2,2,1,1,1)]
 def test_chicago_release_horizon(self):
  sid,i,p,b,c,d,cs=self.base()
  q=qualify(subject=sid,identity=i,expected_identity=i,step=0,policy=p,confidence=Fraction(1,2),budget=b,calibration=c,debt=d,graph={'release':[]},dependency_standing={},candidates=cs,strategy=Strategy.MAX_INFORMATION)
  self.assertEqual((q.state,q.standing,q.selected.name),('READY','UNKNOWN','probe')); self.assertTrue(replay(q.receipt))
  q2=qualify(subject=sid,identity=i,expected_identity=i,step=2,policy=p,confidence=Fraction(19,20),budget=b,calibration=c,debt=d,graph={'release':[]},dependency_standing={},candidates=cs,strategy=Strategy.MAX_INFORMATION)
  self.assertEqual((q2.state,q2.standing,q2.selected),('SATISFIED','PARTIAL_ALIVE',None))
  q3=qualify(subject=sid,identity=i,expected_identity=i,step=1,policy=p,confidence=Fraction(1,2),budget=b,calibration=c,debt=d,graph={'release':['x']},dependency_standing={'x':'BUILD_BROKEN'},candidates=cs,strategy=Strategy.MAX_INFORMATION)
  self.assertEqual((q3.state,q3.standing),('BLOCKED','BLOCKED'))
