import json
import unittest
from scripts.measure_train.dependence_structure_msa.runtime_output import admit_runtime_output
from scripts.measure_train.dependence_structure_msa.subject import Refused
class T(unittest.TestCase):
 def test_empty_and_invalid_runtime_output_refuse(self):
  with self.assertRaisesRegex(Refused,"EMPTY_RUNTIME_OUTPUT"):
   admit_runtime_output("")
  with self.assertRaisesRegex(Refused,"INVALID_RUNTIME_JSON"):
   admit_runtime_output("not-json")
 def test_replay_verified_solved_output_admits(self):
  raw=json.dumps({"standing":"ALIVE","result":{"solved":True,"total_cost":2.0},"evidence":{"replay_verified":True},"worker_sha":"99816fb389670174be44ddaaf3b42f00496e6f21"})
  payload=admit_runtime_output(raw,"99816fb389670174be44ddaaf3b42f00496e6f21")
  self.assertEqual(payload["result"]["total_cost"],2.0)
