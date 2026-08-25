import unittest
from datetime import datetime,timezone
from scripts.measure_train.process_intelligence_projection_qualification_msa.subject import Subject
from scripts.measure_train.process_intelligence_projection_qualification_msa.projection import Projection
from scripts.measure_train.process_intelligence_projection_qualification_msa.observation import ProjectionObservation
from scripts.measure_train.process_intelligence_projection_qualification_msa.methodology import REQUIRED
from scripts.measure_train.process_intelligence_projection_qualification_msa.qualify import qualify
from scripts.measure_train.process_intelligence_projection_qualification_msa.replay import replay
class T(unittest.TestCase):
    def test_all_methods_multi_projection_caps_at_partial_alive(self):
        s=Subject('o/r','a'*40,'b'*64,7); now=datetime.now(timezone.utc); methods=sorted(REQUIRED); rows=[]
        for i in range(22):
            m=methods[i%len(methods)]; p=Projection(f'p{i}',s,m,f'engine{i%3}',f'runtime{i%2}',f'root{i%4}','b'*64,'c'*64); rows.append(ProjectionObservation(p,now,'PASS','EQUIVALENT'))
        q=qualify(s,rows,now); self.assertEqual(q['standing'],'PARTIAL_ALIVE'); self.assertEqual(replay(q['receipt']),'REPLAY_MATCH'); self.assertFalse(q['actuation_performed'])
