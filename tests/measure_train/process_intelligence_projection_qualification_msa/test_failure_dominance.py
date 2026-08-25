import unittest
from datetime import datetime,timezone
from scripts.measure_train.process_intelligence_projection_qualification_msa.subject import Subject
from scripts.measure_train.process_intelligence_projection_qualification_msa.projection import Projection
from scripts.measure_train.process_intelligence_projection_qualification_msa.observation import ProjectionObservation
from scripts.measure_train.process_intelligence_projection_qualification_msa.calibration import Calibration
from scripts.measure_train.process_intelligence_projection_qualification_msa.standing import standing
class T(unittest.TestCase):
    def test_red_dependency_dominates(self):
        s=Subject('o/r','a'*40,'b'*64); now=datetime.now(timezone.utc); o=ProjectionObservation(Projection('p',s,'DISCOVERY','e','r','x','b'*64,'c'*64),now,'PASS','EQUIVALENT')
        self.assertEqual(standing([o],Calibration(20,0.1,'CALIBRATED'),True,['BUILD_BROKEN']),'BUILD_BROKEN')
