import unittest
from scripts.release_train.process_relation_crown import *
from scripts.release_train.process_relation_crown.metamorphic import MetamorphicWitness
from scripts.release_train.process_relation_crown.oracle import OracleWitness
from scripts.release_train.process_relation_crown.rails import Rail,RailEvidence
from scripts.release_train.process_relation_crown.methodology import REQUIRED as METHODS
from scripts.release_train.process_relation_crown.failures import REQUIRED as FAILS
from scripts.release_train.process_relation_crown.selector import Candidate,Strategy
from scripts.release_train.process_relation_crown.receipt import replay
from scripts.release_train.process_relation_crown.refusal import Refused
class T(unittest.TestCase):
 def test_e2e_and_red_rail(self):
  s=Subject.parse("o/r@"+"a"*40); row=RelationCalibration(Relation.PARTIAL_ORDER,3,"c"*64,200,0,2,2)
  f=CalibrationFrontier((row,)); m=MetamorphicWitness(Relation.PARTIAL_ORDER,frozenset({"reflexive","deterministic","independent_commutation"}))
  o=(OracleWitness("i1","m1","v"),OracleWitness("i2","m2","v"))
  rails=tuple(RailEvidence(r,s.canonical,Relation.EXACT,"PASS") for r in Rail)
  qs=qualify(subject=s,row=row,frontier=f,metamorphic=m,oracles=o,candidates=(Candidate(Relation.PARTIAL_ORDER,.03,.04,2,.4),),strategy=Strategy.STRONGEST_DEFENSIBLE,rails=rails,required_relation=Relation.PARTIAL_ORDER,methodologies=METHODS,failure_worlds=FAILS)
  self.assertEqual(qs.standing,"PARTIAL_ALIVE"); self.assertEqual(replay(qs.receipt,qs.receipt.digest),"REPLAY_MATCH")
  bad=list(rails); bad[0]=RailEvidence(bad[0].rail,s.canonical,Relation.EXACT,"FAIL")
  with self.assertRaises(Refused): qualify(subject=s,row=row,frontier=f,metamorphic=m,oracles=o,candidates=(),strategy=Strategy.STRONGEST_DEFENSIBLE,rails=bad,required_relation=Relation.PARTIAL_ORDER,methodologies=METHODS,failure_worlds=FAILS)
