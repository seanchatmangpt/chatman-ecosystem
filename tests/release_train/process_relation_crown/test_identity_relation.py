import unittest
from scripts.release_train.process_relation_crown.subject import Subject
from scripts.release_train.process_relation_crown.relation import Relation,discharges
from scripts.release_train.process_relation_crown.refusal import Refused
class T(unittest.TestCase):
 def test_identity_and_partial_order(self):
  self.assertTrue(Subject.parse("o/r@"+"a"*40))
  with self.assertRaises(Refused): Subject.parse("main")
  self.assertTrue(discharges(Relation.EXACT,Relation.PARTIAL_ORDER))
  self.assertFalse(discharges(Relation.STUTTER,Relation.PARTIAL_ORDER))
