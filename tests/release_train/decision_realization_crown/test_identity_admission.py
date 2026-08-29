import unittest
from scripts.release_train.decision_realization_crown import *
from scripts.release_train.decision_realization_crown.admission import admit
class T(unittest.TestCase):
  def test_identity_and_foreign_generation(self):
    s=Subject.parse("o/r@"+"a"*40); self.assertEqual(s.key,"o/r@"+"a"*40)
    p=DecisionPolicy("p",2,"b"*64,LossMatrix(9,2,1))
    o=Observation("1",1,Decision.INDEPENDENT,True,.1,1,0,0,"discovery","BEAM","us","r")
    with self.assertRaises(Refused): admit(p,[o])
  def test_short_subject_refuses(self):
    with self.assertRaises(Refused): Subject.parse("o/r@abc")
