import unittest
from scripts.release_train.calibrated_composition_crown import *
class T(unittest.TestCase):
 def test_current_and_selectors(self):
  a=Calibration("CONSERVATIVE",2,"a"*64,10,.9,.1,.6); b=Calibration("INDEPENDENT",2,"b"*64,10,.85,.15,.2)
  self.assertIs(current([a],"CONSERVATIVE"),a)
  picks={select([a,b],s).mode for s in Strategy}; self.assertGreaterEqual(len(picks),2)
  self.assertEqual(len(frontier([a,b])),2)
