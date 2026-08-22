import unittest
from scripts.release_train.coherent_epoch_promotion.subject import Subject
from scripts.release_train.coherent_epoch_promotion.census import CensusRow
from scripts.release_train.coherent_epoch_promotion.standing import aggregate_standing
class T(unittest.TestCase):
 def test_failure_dominates(self):
  s=Subject.parse('o/r@'+'a'*40)
  self.assertEqual(aggregate_standing((CensusRow(s,'PARTIAL_ALIVE'),CensusRow(s,'BUILD_BROKEN'))),'BUILD_BROKEN')
