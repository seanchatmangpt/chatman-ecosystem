import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.decision_realization_transport_msa.subject import Subject
from scripts.measure_train.decision_realization_transport_msa.stratum import Stratum
from scripts.measure_train.decision_realization_transport_msa.observation import Observation
from scripts.measure_train.decision_realization_transport_msa.frontier import TransportModel
from scripts.measure_train.decision_realization_transport_msa.qualify import qualify
from scripts.measure_train.decision_realization_transport_msa.replay import replay
class T(unittest.TestCase):
 def test_transport_and_failure_dominance(self):
  s=Subject("o/r","a"*40,"b"*64); now=datetime.now(timezone.utc)
  a=Stratum("DISCOVERY","BEAM","us","r1");b=Stratum("CONFORMANCE","WASM","eu","r2")
  src=[Observation(s,"s1",a,Fraction(1,10),Fraction(1,10),True,now),Observation(s,"s2",b,Fraction(1,5),Fraction(1,5),True,now),Observation(s,"s3",a,Fraction(1,10),Fraction(1,10),True,now),Observation(s,"s4",b,Fraction(1,5),Fraction(1,5),True,now)]
  tgt=[Observation(s,"t1",a,Fraction(1,10),Fraction(1,10),True,now),Observation(s,"t2",b,Fraction(1,5),Fraction(1,5),True,now)]
  m=TransportModel("source","target",1,"c"*64,True)
  q=qualify(s,src,tgt,m);self.assertEqual(q["standing"],"PARTIAL_ALIVE");self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
  q2=qualify(s,src,tgt,m,["BUILD_BROKEN"]);self.assertEqual(q2["standing"],"BUILD_BROKEN")
