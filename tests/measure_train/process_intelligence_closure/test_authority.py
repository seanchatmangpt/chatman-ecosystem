import unittest
from scripts.measure_train.process_intelligence_closure.authority import admit_authority
from scripts.measure_train.process_intelligence_closure.subject import Refused

class T(unittest.TestCase):
    def test_brce_only_do(self):
        self.assertEqual(admit_authority("VERIFY"),"ADMITTED")
        with self.assertRaises(Refused): admit_authority("DO")
        self.assertEqual(admit_authority("DO",{"authority":"BRCE","actuation_performed":True}),"ADMITTED")
