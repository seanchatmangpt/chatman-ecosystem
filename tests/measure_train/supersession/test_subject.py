import unittest
from scripts.measure_train.supersession.subject import Subject, Refused

class TestSubject(unittest.TestCase):
    def test_exact_sha_only(self):
        self.assertEqual(Subject("o/r", "a"*40).sha, "a"*40)
        with self.assertRaises(Refused):
            Subject("o/r", "abc")
