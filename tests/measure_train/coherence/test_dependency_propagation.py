from scripts.measure_train.coherence.subject import Subject, Refusal
from scripts.measure_train.coherence.coherence import Standing
from scripts.measure_train.coherence.dependency import NodeStanding, propagate
import unittest
S=Subject("seanchatmangpt/chatman-ecosystem","24b39444364cb959f92525453de69981ca511af3")
G=Subject("seanchatmangpt/gymact","7ce400e878c1da9b7dc46a81072563ec76ef01f4")
class TestDependency(unittest.TestCase):
 def test_broken_dependency_blocks(self):
  out=propagate([NodeStanding(S,Standing.PARTIAL_ALIVE),NodeStanding(G,Standing.BUILD_BROKEN)],{S.repo:{G.repo}})
  self.assertEqual(out[S.repo],Standing.BLOCKED)
 def test_cycle_refuses(self):
  with self.assertRaisesRegex(Refusal,"DEPENDENCY_CYCLE"):
   propagate([NodeStanding(S,Standing.PARTIAL_ALIVE),NodeStanding(G,Standing.PARTIAL_ALIVE)],{S.repo:{G.repo},G.repo:{S.repo}})
if __name__=="__main__": unittest.main()
