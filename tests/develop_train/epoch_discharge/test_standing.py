import unittest
from scripts.develop_train.epoch_discharge.frontier import ConsumerState
from scripts.develop_train.epoch_discharge.standing import derive_standing
class T(unittest.TestCase):
 def test_positive_ceiling_and_pending(self):
  self.assertEqual(derive_standing((ConsumerState("a","REQUALIFIED","REQUALIFIED"),),True),"PARTIAL_ALIVE")
  self.assertEqual(derive_standing((ConsumerState("a","PENDING_ACK",None),),False),"UNKNOWN")
