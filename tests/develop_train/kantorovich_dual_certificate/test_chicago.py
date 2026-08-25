from fractions import Fraction as F
import unittest
from scripts.develop_train.kantorovich_dual_certificate import *
S=Subject.parse("seanchatmangpt/chatman-ecosystem@"+"a"*40+"#"+"b"*64)
A=FiniteMeasure.from_mapping({"a":F(1,2),"b":F(1,3),"c":F(1,6)})
B=FiniteMeasure.from_mapping({"a":F(1,3),"b":F(1,3),"c":F(1,3)})
COST={(a,b):(0 if a==b else (1 if {a,b}!={"a","c"} else 2)) for a in ("a","b","c") for b in ("a","b","c")}
M=GroundMetric.from_mapping(("a","b","c"),COST)
CAL=Calibration(3,"c"*64,20,F(19,20),F(0),F(1,20))
ENG=[EngineWitness("BEAM","impl-beam","model-beam","s","t","o"),EngineWitness("WASM","impl-wasm","model-wasm","s","t","o")]
ORC=[OracleWitness("powl","p1","ip1","mp1","d"),OracleWitness("powl","p2","ip2","mp2","d"),OracleWitness("ocel","o1","io1","mo1","e"),OracleWitness("ocel","o2","io2","mo2","e")]
class T(unittest.TestCase):
    def test_complete_process_transport_certificate(self):
        result=qualify(S,A,B,M,CAL,REQUIRED,ENG,ORC,list(World))
        self.assertEqual(result.standing,"PARTIAL_ALIVE"); self.assertEqual(result.dual_gap,0); self.assertEqual(replay(result.receipt,result.receipt.digest),"REPLAY_MATCH")
        red=qualify(S,A,B,M,CAL,REQUIRED,ENG,ORC,list(World),("BUILD_BROKEN",))
        self.assertEqual(red.standing,"BUILD_BROKEN"); self.assertIsNone(red.receipt)
