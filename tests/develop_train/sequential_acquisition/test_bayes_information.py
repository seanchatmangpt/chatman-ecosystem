import unittest
from datetime import datetime, timezone
from fractions import Fraction
from scripts.develop_train.sequential_acquisition.belief import BeliefState
from scripts.develop_train.sequential_acquisition.evidence import ObservationEvidence
from scripts.develop_train.sequential_acquisition.bayes import update
from scripts.develop_train.sequential_acquisition.information import realized_information

class BayesInformationCourt(unittest.TestCase):
    def test_update_concentrates_and_realizes_information(self):
        p = BeliefState(0,{"g":Fraction(1,2),"b":Fraction(1,2)})
        e = ObservationEvidence("s","o",datetime.now(timezone.utc),{"g":Fraction(9,10),"b":Fraction(1,10)},Fraction(1),Fraction(1))
        q = update(p,e)
        self.assertEqual(q.probabilities["g"], Fraction(9,10))
        self.assertGreater(realized_information(p,q,0.4).realized_bits,0)
