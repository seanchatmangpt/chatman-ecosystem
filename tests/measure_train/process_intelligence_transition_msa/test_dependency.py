import unittest
from scripts.measure_train.process_intelligence_transition_msa.obligation import Obligation
from scripts.measure_train.process_intelligence_transition_msa.dependency import obligation_dependency_graph
from scripts.measure_train.process_intelligence_transition_msa.blockers import propagated_states

class T(unittest.TestCase):
    def test_red_parent_blocks_green_consumer(self):
        obs=[Obligation("reactor","REACTOR"),Obligation("replay","REPLAY")]
        g=obligation_dependency_graph(obs,[("replay","reactor")])
        census=(("reactor","REACTOR",True,"FAIL"),("replay","REPLAY",True,"PASS"))
        self.assertEqual(propagated_states(census,g)["replay"],"BLOCKED")
