import unittest
from scripts.release_train.ack_discharge_promotion.subject import Subject
from scripts.release_train.ack_discharge_promotion.graph import DependencyGraph, GraphRefusal
A=Subject.parse("o/a@"+"a"*40); B=Subject.parse("o/b@"+"b"*40); C=Subject.parse("o/c@"+"c"*40)
class T(unittest.TestCase):
    def test_depth(self): self.assertEqual(DependencyGraph(((A,B),(B,C))).affected(A),((B,1),(C,2)))
    def test_cycle(self):
        with self.assertRaises(GraphRefusal): DependencyGraph(((A,B),(B,A)))
