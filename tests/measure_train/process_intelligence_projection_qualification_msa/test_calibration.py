import unittest
from datetime import datetime,timezone
from scripts.measure_train.process_intelligence_projection_qualification_msa.subject import Subject
from scripts.measure_train.process_intelligence_projection_qualification_msa.projection import Projection
from scripts.measure_train.process_intelligence_projection_qualification_msa.observation import ProjectionObservation
from scripts.measure_train.process_intelligence_projection_qualification_msa.calibration import calibrate
class T(unittest.TestCase):
    def test_false_equivalent_bounded(self):
        s=Subject('o/r','a'*40,'b'*64); now=datetime.now(timezone.utc)
        rows=[ProjectionObservation(Projection(str(i),s,'DISCOVERY',f'e{i}',f'r{i}',f'x{i}','b'*64,'c'*64),now,'PASS','EQUIVALENT') for i in range(20)]
        self.assertEqual(calibrate(rows).state,'CALIBRATED')
