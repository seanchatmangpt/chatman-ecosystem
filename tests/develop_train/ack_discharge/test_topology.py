import unittest
from scripts.develop_train.ack_discharge.subject import Subject
from scripts.develop_train.ack_discharge.topology import *
class T(unittest.TestCase):
 def test_depth_cycle(self):
  p=Subject('o/p','a'*40);a=ConsumerNode(Subject('o/a','b'*40));b=ConsumerNode(Subject('o/b','c'*40),True)
  g=DependencyTopology(p,[a,b],[(p.identity,a.subject.identity),(a.subject.identity,b.subject.identity)])
  self.assertEqual([d for _,d in g.affected()],[1,2])
  with self.assertRaises(RefusedTopology):DependencyTopology(p,[a,b],[(p.identity,a.subject.identity),(a.subject.identity,b.subject.identity),(b.subject.identity,a.subject.identity)])
