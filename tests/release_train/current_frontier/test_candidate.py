import unittest
from scripts.release_train.current_frontier.candidate import Candidate, select, Refusal
from scripts.release_train.current_frontier.admission import Admission
class T(unittest.TestCase):
 def test_deterministic_selection(self):
  a=Admission("o/r@"+"a"*40,"PARTIAL_ALIVE",(),True,()); c1=Candidate("x",(a,),1,10,2); c2=Candidate("y",(a,),2,10,2); self.assertEqual(select((c1,c2)).name,"y")
 def test_blocked_refuses(self):
  a=Admission("o/r@"+"a"*40,"BUILD_BROKEN",(),False,("bad",))
  with self.assertRaises(Refusal): select((Candidate("x",(a,),1,1,1),))
