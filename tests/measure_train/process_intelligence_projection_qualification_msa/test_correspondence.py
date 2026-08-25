import unittest
from scripts.measure_train.process_intelligence_projection_qualification_msa.subject import Subject
from scripts.measure_train.process_intelligence_projection_qualification_msa.projection import Projection
from scripts.measure_train.process_intelligence_projection_qualification_msa.correspondence import require_equivalent
from scripts.measure_train.process_intelligence_projection_qualification_msa.refusal import Refused
class T(unittest.TestCase):
    def test_divergence_refuses(self):
        s=Subject('o/r','a'*40,'b'*64); a=Projection('a',s,'DISCOVERY','e1','r1','x','b'*64,'c'*64); b=Projection('b',s,'DISCOVERY','e2','r2','y','b'*64,'d'*64)
        with self.assertRaises(Refused): require_equivalent(a,b)
