import unittest
from fractions import Fraction
from scripts.develop_train.fused_acquisition.calibration import Calibration
from scripts.develop_train.fused_acquisition.sensor import Sensor
from scripts.develop_train.fused_acquisition.independence import IndependenceProof,admitted_pairs,maximum_independent_subset
from scripts.develop_train.fused_acquisition.refusals import Refused
def s(i,f,d): return Sensor(i,f,d,Calibration(1,(i[-1]*64),10,Fraction(0),Fraction(0),Fraction(0)))
class TestIndependence(unittest.TestCase):
 def test_explicit_independence_and_clique(self):
  xs=[s('s1','f1','d1'),s('s2','f2','d2'),s('s3','f3','d3')]
  ps=[IndependenceProof('s1','s2','a'*64),IndependenceProof('s1','s3','b'*64),IndependenceProof('s2','s3','c'*64)]
  pairs=admitted_pairs(xs,ps); self.assertEqual(maximum_independent_subset(xs,pairs),('s1','s2','s3'))
  with self.assertRaises(Refused): admitted_pairs([s('s1','same','d1'),s('s2','same','d2')],[IndependenceProof('s1','s2','d'*64)])
