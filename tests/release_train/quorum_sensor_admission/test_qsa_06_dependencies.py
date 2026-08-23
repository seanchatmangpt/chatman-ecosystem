import unittest
from scripts.release_train.quorum_sensor_admission import DependencyGraph, Refused, Subject
from common import SUBJECT, DEP
class DependencyCourt(unittest.TestCase):
 def test_transitive_red_dependency_visible(self):
  leaf=Subject.parse(f"seanchatmangpt/ex4pm@{'d'*40}"); g=DependencyGraph({SUBJECT:(DEP,),DEP:(leaf,),leaf:()},{DEP:"ALIVE",leaf:"BUILD_BROKEN"}); self.assertIn("BUILD_BROKEN",g.blockers(SUBJECT)[0])
 def test_cycle_refuses(self):
  with self.assertRaises(Refused): DependencyGraph({SUBJECT:(DEP,),DEP:(SUBJECT,)},{}).validate(SUBJECT)
if __name__=="__main__": unittest.main()
