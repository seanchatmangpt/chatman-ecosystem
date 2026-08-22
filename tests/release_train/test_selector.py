import unittest
from scripts.release_train.selector import Candidate,select,SelectionRefusal
from scripts.release_train.graph import Edge

class SelectorTests(unittest.TestCase):
    def test_release_criticality_is_primary(self):
        low=Candidate("a","a",10,10,10,1); high=Candidate("b","b",1,1,1,2)
        self.assertEqual(select([low,high],[])[0].key,"b")
    def test_returns_dependency_closure(self):
        c=Candidate("x","b",1,1,1,1)
        self.assertEqual(select([c],[Edge("a","b")])[1],("a","b"))
    def test_no_viable_candidate_blocks(self):
        with self.assertRaisesRegex(SelectionRefusal,"NO_IMPLEMENTABLE"):
            select([Candidate("x","x",1,1,1,1,True)],[])
