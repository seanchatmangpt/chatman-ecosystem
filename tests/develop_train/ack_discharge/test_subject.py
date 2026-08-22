import unittest
from scripts.develop_train.ack_discharge.subject import Subject,RefusedSubject
class T(unittest.TestCase):
 def test_identity(self):
  self.assertEqual(Subject('o/r','a'*40).identity,'o/r@'+'a'*40)
  with self.assertRaises(RefusedSubject):Subject('o/r','a'*7)
