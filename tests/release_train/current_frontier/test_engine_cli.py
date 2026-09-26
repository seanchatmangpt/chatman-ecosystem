"""current_frontier CLI end to end: a real child interpreter reads stdin, prints JSON.

Chicago style (following tests/release_train/ack_discharge_promotion/test_e2e.py): the
real ``python -m scripts.release_train.current_frontier.cli`` runs in a subprocess with
the payload on its real stdin; assertions are on the real stdout JSON. Nothing is patched.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CMD = [sys.executable, "-m", "scripts.release_train.current_frontier.cli"]


class T(unittest.TestCase):
    def payload(self):
        return {"predecessor": "124aaaca626ff239c97b9a18cc91cd5d525a8c60", "evidence": {"lib": [{"id": "l", "subject": "o/lib@" + "a" * 40, "scope": "REPOSITORY", "outcome": "PASS", "observed_at": "2026-08-22T10:00:00Z", "run_id": "1"}], "app": [{"id": "a", "subject": "o/app@" + "b" * 40, "scope": "REPOSITORY", "outcome": "PASS", "observed_at": "2026-08-22T10:00:01Z", "run_id": "2"}]}, "supersession": {}, "obligations": [{"obligation_id": "repo", "required_scope": "REPOSITORY", "required": True}], "graph": {"lib": [], "app": ["lib"]}}

    def invoke(self):
        done = subprocess.run(CMD, input=json.dumps(self.payload()), text=True, capture_output=True, check=True, cwd=REPO)
        return done.stdout

    def test_deterministic_e2e(self):
        one = self.invoke()
        two = self.invoke()
        self.assertEqual(one, two)
        decoded = json.loads(one)
        self.assertEqual(decoded["plan"]["phases"], ["VERIFY", "CONSTRUCT"])
        self.assertFalse(decoded["receipt"]["body"]["actuation_performed"])


if __name__ == "__main__":
    unittest.main()
