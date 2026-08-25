import unittest
from scripts.measure_train.supersession.relation import Supersession
from scripts.measure_train.supersession.subject import Refused

class TestRelation(unittest.TestCase):
    def test_reason_is_bounded(self):
        self.assertEqual(Supersession("n","o","NEW_RUN").reason,"NEW_RUN")
        with self.assertRaises(Refused):
            Supersession("n","o","MAGIC")
