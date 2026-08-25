import unittest
from scripts.release_train.process_relation_crown.calibration import RelationCalibration
from scripts.release_train.process_relation_crown.relation import Relation
from scripts.release_train.process_relation_crown.frontier import CalibrationFrontier
from scripts.release_train.process_relation_crown.oracle import OracleWitness,require_independent
from scripts.release_train.process_relation_crown.refusal import Refused
class T(unittest.TestCase):
 def test_currentness_and_independence(self):
  a=RelationCalibration(Relation.EXACT,1,"a"*64,100,0,0,1); b=RelationCalibration(Relation.EXACT,2,"b"*64,100,0,0,1)
  f=CalibrationFrontier((a,b)); self.assertEqual(f.current(Relation.EXACT),b)
  with self.assertRaises(Refused): f.require(a)
  require_independent(OracleWitness("i1","m1","v"),OracleWitness("i2","m2","v"))
  with self.assertRaises(Refused): require_independent(OracleWitness("i","m1","v"),OracleWitness("i","m2","v"))
