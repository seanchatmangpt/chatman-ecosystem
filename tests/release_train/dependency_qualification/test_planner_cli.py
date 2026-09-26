"""dependency_qualification CLI end to end: a real child interpreter reads stdin, prints JSON.

Chicago style (following tests/release_train/ack_discharge_promotion/test_e2e.py): the
real ``python -m scripts.release_train.dependency_qualification.cli`` runs in a subprocess
with the payload on its real stdin; assertions are on the real stdout JSON.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CMD = [sys.executable, "-m", "scripts.release_train.dependency_qualification.cli"]


class T(unittest.TestCase):
    def test_e2e_deterministic(self):
        d = {"allowed_repos": ["seanchatmangpt/clap-noun-verb"], "allowed_licenses": ["MIT", "CC0-1.0"], "candidates": [{"repo": "seanchatmangpt/clap-noun-verb", "sha": "31e55ec0440f48b91ff6c5e08b0946c837b98c63", "criticality": 9, "blockers_removed": 3, "evidence": "exact-head-success"}], "edges": {"seanchatmangpt/clap-noun-verb": []}}
        raw = json.dumps(d)
        outs = [
            subprocess.run(CMD, input=raw, text=True, capture_output=True, check=True, cwd=REPO).stdout for _ in range(2)
        ]
        self.assertEqual(outs[0], outs[1])
        decoded = json.loads(outs[0])
        self.assertIn("actuation_performed", outs[0])
        self.assertEqual(set(decoded), {"plan", "receipt"})


if __name__ == "__main__":
    unittest.main()
