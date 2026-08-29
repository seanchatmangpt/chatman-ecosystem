import unittest
from fixture import *
from scripts.release_train.feedback_policy_admission.dependency import DependencyGraph
class T(unittest.TestCase):
 def test_transitive_blocker(self):
  g=DependencyGraph({"root":("mid",),"mid":("leaf",)},{"leaf":"BUILD_BROKEN"})
  self.assertEqual(g.blockers("root"),("leaf",))
if __name__=="__main__": unittest.main()
