import unittest
from scripts.measure_train.blockers import *
from scripts.measure_train.identity import *
class BlockerCourt(unittest.TestCase):
    def setUp(self): self.a=Subject('o/a','a'*40); self.b=Subject('o/b','b'*40)
    def test_broken_dependency_blocks_parent(self):
        g=DependencyGraph({self.a:(self.b,),self.b:()}); self.assertEqual(propagate(g,{self.a:Standing.PARTIAL_ALIVE,self.b:Standing.BUILD_BROKEN})[self.a],Standing.BLOCKED)
    def test_unknown_not_success(self):
        g=DependencyGraph({self.a:(self.b,),self.b:()}); self.assertEqual(propagate(g,{self.a:Standing.PARTIAL_ALIVE})[self.a],Standing.UNKNOWN)
    def test_cycle_refuses(self):
        with self.assertRaises(Refused): DependencyGraph({self.a:(self.b,),self.b:(self.a,)}).order()
if __name__=='__main__': unittest.main()
