import json,tempfile,unittest
from pathlib import Path
from scripts.release_train.cli import main

class CliTests(unittest.TestCase):
    def test_manufacture_then_replay(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); inp=td/"in.json"; out=td/"out.json"
            inp.write_text(json.dumps({
              "since":"2026-08-22T03:00:00Z","until":"2026-08-22T05:00:00Z",
              "evidence":[],"dependencies":[],"candidates":[{"key":"C","repo":"o/r","value":1,"reversibility":1,"evidence":1,"release_criticality":1}],
              "actions":[{"kind":"VERIFY","target":"x"}],"gates":[]
            }))
            self.assertEqual(main(["manufacture","--input",str(inp),"--output",str(out)]),0)
            first=out.read_bytes()
            self.assertEqual(main(["manufacture","--input",str(inp),"--output",str(out)]),0)
            self.assertEqual(first,out.read_bytes())
            self.assertEqual(main(["replay","--receipt",str(out)]),0)
