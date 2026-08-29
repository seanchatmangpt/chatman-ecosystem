import unittest
from scripts.release_train.ack_discharge_promotion.subject import Subject
from scripts.release_train.ack_discharge_promotion.census import CensusRow
from scripts.release_train.ack_discharge_promotion.standing import standing
S=Subject.parse("o/r@"+"a"*40)
class T(unittest.TestCase):
    def test_pending_unknown(self): self.assertEqual(standing((CensusRow(S,1,"PENDING_ACK",None),),False),"UNKNOWN")
    def test_positive_ceiling(self): self.assertEqual(standing((CensusRow(S,1,"REQUALIFIED","REQUALIFIED"),),True),"PARTIAL_ALIVE")
