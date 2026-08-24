import unittest
from scripts.measure_train.process_intelligence_projection_qualification_msa.subject import Subject
from scripts.measure_train.process_intelligence_projection_qualification_msa.frontier import current_frontier
from scripts.measure_train.process_intelligence_projection_qualification_msa.dependency import graph
from scripts.measure_train.process_intelligence_projection_qualification_msa.refusal import Refused
class T(unittest.TestCase):
    def test_split_and_cycle_refuse(self):
        a=Subject('o/r','a'*40,'b'*64,1); b=Subject('o/r','c'*40,'b'*64,1)
        with self.assertRaises(Refused): current_frontier([a,b])
        with self.assertRaises(Refused): graph(['a','b'],[('a','b'),('b','a')])
