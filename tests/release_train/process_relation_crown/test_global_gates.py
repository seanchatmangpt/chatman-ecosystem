import unittest
from datetime import datetime,timezone
from scripts.release_train.process_relation_crown.methodology import require_complete as rm,REQUIRED as METHODS
from scripts.release_train.process_relation_crown.failures import require_complete as rf,REQUIRED as FAILS
from scripts.release_train.process_relation_crown.distributed import HostWitness,require_current
from scripts.release_train.process_relation_crown.refusal import Refused
class T(unittest.TestCase):
 def test_methodology_failure_tls(self):
  rm(METHODS); rf(FAILS); now=datetime.now(timezone.utc)
  rows=[HostWitness("h1","r1","s","t",True,"c1",now),HostWitness("h2","r2","s","t",True,"c2",now)]
  require_current(rows,now)
  with self.assertRaises(Refused): require_current([rows[0],HostWitness("h2","r2","s","t",False,"",now)],now)
