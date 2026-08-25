import unittest
from fractions import Fraction
from scripts.develop_train.process_transition_substrate import *
class T(unittest.TestCase):
 def test_blockers(self):
  g=DependencyGraph({"distributed":("reactor",),"reactor":("semantic",)})
  st={"semantic":State.PASS,"reactor":State.FAIL,"distributed":State.UNKNOWN}
  self.assertEqual(g.blockers(st,"distributed"),("reactor",))
 def test_census(self):
  c=census([Obligation("a",State.PASS,"x"),Obligation("b",State.UNKNOWN,"x")])
  self.assertEqual(c["closure"],Fraction(1,2))
