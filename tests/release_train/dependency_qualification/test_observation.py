import unittest
from scripts.release_train.dependency_qualification import DependencySubject
from scripts.release_train.dependency_qualification.observation import DependencyObservation
class T(unittest.TestCase):
 def test_standing(self):
  s=DependencySubject('o/r','a'*40); self.assertEqual(DependencyObservation(s,'Verify','success','t').standing(),'PARTIAL_ALIVE'); self.assertEqual(DependencyObservation(s,'Verify','failure','t').standing(),'BUILD_BROKEN')
