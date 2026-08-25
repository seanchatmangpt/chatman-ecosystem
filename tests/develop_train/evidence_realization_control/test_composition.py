import unittest
from scripts.develop_train.evidence_realization_control import *
class T(unittest.TestCase):
 def test_dependence_changes_operator(self):
  s=Subject.parse('o/r@'+'b'*40); a=EvidenceNode('a',s,'semantic',1,Interval(.8,.9),'i1','m1','d1'); b=EvidenceNode('b',s,'trace',1,Interval(.8,.9),'i2','m2','d2'); self.assertNotEqual(compose(a,b).lo,compose(a,b,True).lo)
 def test_alias_refuses(self):
  s=Subject.parse('o/r@'+'b'*40); a=EvidenceNode('a',s,'semantic',1,Interval(.8,.9),'i1','m1','d1'); b=EvidenceNode('b',s,'trace',1,Interval(.8,.9),'i1','m2','d2')
  with self.assertRaises(Refused): compose(a,b,True)
