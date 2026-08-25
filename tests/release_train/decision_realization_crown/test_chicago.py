import unittest
from fractions import Fraction
from scripts.release_train.decision_realization_crown import *
from scripts.release_train.decision_realization_crown.failures import REQUIRED
from scripts.release_train.decision_realization_crown.drift import Cusum
class T(unittest.TestCase):
  def test_full_realization_is_bounded_and_replayable(self):
    s=Subject.parse("o/r@"+"a"*40); p=DecisionPolicy("p",1,"b"*64,LossMatrix(9,2,1)); obs=[]
    for i,m in enumerate(sorted(REQUIRED_METHODOLOGIES)):
      obs.append(Observation(str(i),1,Decision.INDEPENDENT,True,Fraction(0),1,0,0,m,"BEAM" if i%2==0 else "WASM","us" if i%2==0 else "eu","r"+str(i)))
    cal=Calibration(1,"c"*64,len(obs),Fraction(0),Fraction(1,5))
    eng=[EngineWitness("BEAM","1"*64,"2"*64,"3"*64,"4"*64),EngineWitness("WASM","5"*64,"6"*64,"3"*64,"4"*64)]
    ors=[OracleWitness("POWL","1"*64,"2"*64,"p1"),OracleWitness("POWL","3"*64,"4"*64,"p2"),OracleWitness("OCEL","5"*64,"6"*64,"o1"),OracleWitness("OCEL","7"*64,"8"*64,"o2")]
    reg=[RegionWitness("h1","us",True,"a"*64,True),RegionWitness("h2","eu",True,"b"*64,True)]
    q=qualify(subject=s,policy=p,observations=obs,calibration=cal,drift=Cusum(0,1,0),engines=eng,oracles=ors,regions=reg,failure_worlds=REQUIRED,dependency_graph={"release":()},dependency_standing={})
    self.assertEqual(q.standing,"PARTIAL_ALIVE"); self.assertEqual(replay(q.receipt),"REPLAY_MATCH")
  def test_red_dependency_blocks_receipt(self):
    s=Subject.parse("o/r@"+"a"*40); p=DecisionPolicy("p",1,"b"*64,LossMatrix(9,2,1)); o=Observation("1",1,Decision.INDEPENDENT,True,0,1,0,0,"discovery","BEAM","us","r"); cal=Calibration(1,"c"*64,8,0,Fraction(1,5))
    q=qualify(subject=s,policy=p,observations=[o],calibration=cal,drift=Cusum(0,1,0),engines=[],oracles=[],regions=[],failure_worlds=(),dependency_graph={"release":("x",)},dependency_standing={"x":"BUILD_BROKEN"})
    self.assertEqual(q.standing,"BLOCKED"); self.assertIsNone(q.receipt)
