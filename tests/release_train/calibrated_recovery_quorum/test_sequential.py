import unittest
from scripts.release_train.calibrated_recovery_quorum.likelihood import LikelihoodContribution
from scripts.release_train.calibrated_recovery_quorum.sequential import decide
class T(unittest.TestCase):
 def test_decisions(self):
  self.assertEqual(decide([LikelihoodContribution(3,True)]).decision,"ACCEPT_BOUNDED")
  self.assertEqual(decide([LikelihoodContribution(0,False)]).decision,"CONTINUE")
