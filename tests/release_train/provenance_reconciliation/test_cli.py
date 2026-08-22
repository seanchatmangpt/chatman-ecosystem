import json, subprocess, sys, unittest
from tests.release_train.provenance_reconciliation.helpers import SHA_A,DIGEST

class CliCourt(unittest.TestCase):
    def payload(self):
        repo="seanchatmangpt/chatman-ecosystem"; subject={"repo":repo,"sha":SHA_A}; scopes=("focused","integration","e2e","replay","security","repository")
        return {"predecessor_sha":"f"*40,"window":{"start":"2026-08-22T08:00:00Z","end":"2026-08-22T10:00:00Z"},"records":[{"evidence_id":f"{repo}:{s}","subject":subject,"kind":"ci_run","observed_at":"2026-08-22T09:00:00Z","source_uri":"https://api.github.com/example","digest_sha256":DIGEST,"run_id":i+1} for i,s in enumerate(scopes)],"claims":[{"claim_id":f"c:{s}","subject":subject,"scope":s,"standing":"ALIVE","evidence_ids":[f"{repo}:{s}"]} for s in scopes],"subjects":[subject]}
    def test_cli_is_deterministic(self):
        raw=json.dumps(self.payload()).encode(); cmd=[sys.executable,"-m","scripts.release_train.provenance_reconciliation.cli"]
        a=subprocess.run(cmd,input=raw,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False); b=subprocess.run(cmd,input=raw,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
        self.assertEqual(0,a.returncode,a.stderr); self.assertEqual(a.stdout,b.stdout); self.assertEqual("PARTIAL_ALIVE",json.loads(a.stdout)["standing"])
if __name__ == "__main__": unittest.main()
