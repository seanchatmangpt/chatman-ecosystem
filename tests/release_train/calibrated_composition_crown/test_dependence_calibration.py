import unittest
from scripts.release_train.calibrated_composition_crown import *
class T(unittest.TestCase):
 def test_modes_and_calibration(self):
  a,b=Interval(.7,.9),Interval(.6,.8); p=Provenance("i","m","d"); q=Provenance("j","n","e")
  self.assertNotEqual(compose(a,b,Mode.CONSERVATIVE),compose(a,b,Mode.INDEPENDENT,p,q))
  c=calibrate("CONSERVATIVE",1,"a"*64,[Case(.2,.8,.5)]*5); self.assertEqual(c.coverage,1)
 def test_alias_refuses(self):
  p=Provenance("i","m","d")
  with self.assertRaises(Refused): compose(Interval(.5,.8),Interval(.5,.8),Mode.INDEPENDENT,p,p)
