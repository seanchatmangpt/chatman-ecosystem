import io,json,unittest
from unittest.mock import patch
from scripts.release_train.dependency_qualification.cli import main
class T(unittest.TestCase):
 def test_e2e_deterministic(self):
  d={'allowed_repos':['seanchatmangpt/clap-noun-verb'],'allowed_licenses':['MIT','CC0-1.0'],'candidates':[{'repo':'seanchatmangpt/clap-noun-verb','sha':'31e55ec0440f48b91ff6c5e08b0946c837b98c63','criticality':9,'blockers_removed':3,'evidence':'exact-head-success'}],'edges':{'seanchatmangpt/clap-noun-verb':[]}}
  raw=json.dumps(d); outs=[]
  for _ in range(2):
   o=io.StringIO()
   with patch('sys.stdin',io.StringIO(raw)), patch('sys.stdout',o): self.assertEqual(main([]),0)
   outs.append(o.getvalue())
  self.assertEqual(outs[0],outs[1]); self.assertIn('actuation_performed',outs[0])
