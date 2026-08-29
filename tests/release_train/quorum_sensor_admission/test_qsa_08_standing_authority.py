import unittest
from scripts.release_train.quorum_sensor_admission import ActionClass, Refused, admit_action
from scripts.release_train.quorum_sensor_admission.standing import bounded_standing
from scripts.release_train.quorum_sensor_admission.topology import Topology
class StandingAuthorityCourt(unittest.TestCase):
 def test_positive_never_manufactures_alive(self): self.assertEqual(bounded_standing(Topology.HEALTHY,(),True)[0],"PARTIAL_ALIVE")
 def test_do_requires_brce(self):
  with self.assertRaises(Refused): admit_action(ActionClass.DO)
  admit_action(ActionClass.SELECT)
if __name__=="__main__": unittest.main()
