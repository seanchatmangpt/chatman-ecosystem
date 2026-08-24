from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.develop_train.federation_epistemic_capital_control import *
import unittest
class T(unittest.TestCase):
 def test_select_correspond(self):
  cs=[Candidate('a',Fraction(3),Fraction(1,5),Fraction(2),False),Candidate('b',Fraction(2),Fraction(0),Fraction(1),True)]
  self.assertEqual(select(cs,Strategy.MAX_EFFECTIVE_GAIN).transport_id,'a')
  self.assertEqual(select(cs,Strategy.MIN_CORRELATION).transport_id,'b')
  self.assertEqual(select(cs,Strategy.COVERAGE_FIRST).transport_id,'b')
  self.assertTrue(require_engines([EngineWitness('BEAM','i1','s','t','o'),EngineWitness('WASM','i2','s','t','o')]))
  self.assertTrue(require_regions([RegionWitness('h1','r1',9,'s',True,'c1'),RegionWitness('h2','r2',9,'s',True,'c2')]))
