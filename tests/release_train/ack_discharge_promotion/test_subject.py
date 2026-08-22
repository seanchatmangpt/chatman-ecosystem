import unittest
from scripts.release_train.ack_discharge_promotion.subject import Subject, SubjectRefusal
class T(unittest.TestCase):
    def test_exact(self): self.assertEqual(Subject.parse("o/r@"+"a"*40).sha,"a"*40)
    def test_refuse(self):
        with self.assertRaises(SubjectRefusal): Subject.parse("o/r@main")
