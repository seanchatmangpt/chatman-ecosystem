import unittest
from datetime import datetime,timezone
from scripts.measure_train.manifest_reference_observability_msa.transport import TransportIdentity
from scripts.measure_train.manifest_reference_observability_msa.observation import RefObservation
from scripts.measure_train.manifest_reference_observability_msa.independence import IndependenceWitness
from scripts.measure_train.manifest_reference_observability_msa.quorum import exact_quorum
from scripts.measure_train.manifest_reference_observability_msa.frontier import current_transport_frontier
from scripts.measure_train.manifest_reference_observability_msa.refusal import Refused

class T(unittest.TestCase):
 def test_independent_exact_quorum_and_split_frontier(self):
  now=datetime.now(timezone.utc)
  a=TransportIdentity("api",1,"a"*64,"b"*64,"api")
  b=TransportIdentity("git",1,"c"*64,"d"*64,"git")
  rows=[RefObservation("x",a,"RESOLVED",now,5,"e"*40,"EXACT","1"),RefObservation("x",b,"RESOLVED",now,6,"e"*40,"EXACT","2")]
  w=IndependenceWitness("api","git",True,True,True)
  self.assertEqual(exact_quorum("x",rows,[w]),"QUORUM_EXACT")
  split=TransportIdentity("api",1,"f"*64,"b"*64,"api")
  with self.assertRaises(Refused):
   current_transport_frontier(rows+[RefObservation("x",split,"RESOLVED",now,7,"e"*40,"EXACT","3")])
