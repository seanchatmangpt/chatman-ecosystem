import unittest
from scripts.release_train.process_relation_crown.calibration import RelationCalibration
from scripts.release_train.process_relation_crown.relation import Relation
from scripts.release_train.process_relation_crown.admission import admit,Thresholds
from scripts.release_train.process_relation_crown.metamorphic import MetamorphicWitness
from scripts.release_train.process_relation_crown.refusal import Refused
class T(unittest.TestCase):
 def test_bounds_and_laws(self):
  r=RelationCalibration(Relation.EXACT,1,"a"*64,100,0,1,1.0)
  self.assertLess(r.fe_upper,.05)
  admit(r,MetamorphicWitness(Relation.EXACT,frozenset({"reflexive","deterministic"})),Thresholds())
  with self.assertRaises(Refused): admit(r,MetamorphicWitness(Relation.EXACT,frozenset({"reflexive"})))
