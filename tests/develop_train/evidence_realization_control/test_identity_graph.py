import unittest
from scripts.develop_train.evidence_realization_control import *
class T(unittest.TestCase):
 def test_identity_graph(self):
  s=Subject.parse('seanchatmangpt/chatman-ecosystem@'+'a'*40); a=EvidenceNode('a',s,'semantic',1,Interval(.8,.9),'i1','m1','d1'); b=EvidenceNode('b',s,'trace',1,Interval(.7,.9),'i2','m2','d2'); self.assertEqual(EvidenceGraph([a,b],[('a','b')]).order,('a','b'))
 def test_cycle(self):
  s=Subject.parse('seanchatmangpt/chatman-ecosystem@'+'a'*40); a=EvidenceNode('a',s,'semantic',1,Interval(.8,.9),'i1','m1','d1'); b=EvidenceNode('b',s,'trace',1,Interval(.7,.9),'i2','m2','d2')
  with self.assertRaises(Refused): EvidenceGraph([a,b],[('a','b'),('b','a')])
