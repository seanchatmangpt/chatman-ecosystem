import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.process_intelligence_projection_qualification_msa.subject import Subject
from scripts.measure_train.process_intelligence_projection_qualification_msa.projection import Projection
from scripts.measure_train.process_intelligence_projection_qualification_msa.observation import ProjectionObservation
from scripts.measure_train.process_intelligence_projection_qualification_msa.admission import admit
from scripts.measure_train.process_intelligence_projection_qualification_msa.refusal import Refused
class T(unittest.TestCase):
    def test_future_refuses(self):
        s=Subject('o/r','a'*40,'b'*64); now=datetime.now(timezone.utc); p=Projection('p',s,'DISCOVERY','e','r','root','b'*64,'c'*64)
        with self.assertRaises(Refused): admit(s,[ProjectionObservation(p,now+timedelta(seconds=1),'PASS','EQUIVALENT')],now)
